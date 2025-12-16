  #!/usr/bin/env python3
import sys
import re

service_file = sys.argv[1]
domain_file = sys.argv[2]
infra_file = sys.argv[3]
class_name = sys.argv[4]
file_name = sys.argv[5]
directory_name = sys.argv[6]

# Leer el service
with open(service_file, 'r') as f:
    service_content = f.read()

# Extraer imports de models del service
model_imports = set()
import_pattern = r'import\s*{([^}]+)}\s*from\s*[\'"]@/app/domain/models/([^\'"]+)[\'"];'
for match in re.finditer(import_pattern, service_content):
    imports = match.group(1).strip()
    path = match.group(2).strip()
    model_imports.add(f"import {{{imports}}} from '@/app/domain/models/{path}';")

# Extraer métodos con sus parámetros y tipos de retorno
method_pattern = r'async\s+(\w+)\s*\(([^)]*)\)\s*:\s*Promise<([^>]+)>\s*{'
methods = []

for match in re.finditer(method_pattern, service_content):
    method_name = match.group(1)
    params = match.group(2).strip()
    return_type = match.group(3).strip()

    if not method_name.startswith('_'):  # Ignorar métodos privados
        methods.append({
            'name': method_name,
            'params': params,
            'return_type': return_type
        })

# Generar domain repository (interface)
domain_content = []
domain_content.append("// Imports de models")
for import_line in sorted(model_imports):
    domain_content.append(import_line)
domain_content.append("")
domain_content.append(f"export abstract class {class_name} {{")

for method in methods:
    domain_content.append(f"  abstract {method['name']}({method['params']}): Promise<{method['return_type']}>;")

domain_content.append("}")

# Escribir domain repository
with open(domain_file, 'w') as f:
    f.write('\n'.join(domain_content))

# Generar implementation repository
impl_class_name = class_name.replace('Repository', 'ImplementationRepository')
impl_content = []
impl_content.append("import { Injectable } from '@angular/core';")
impl_content.append(f"import {{{class_name}}} from '@/app/domain/repositories/{directory_name}/{file_name}.repository';")

for import_line in sorted(model_imports):
    impl_content.append(import_line)

impl_content.append(f"import {{{class_name.replace('Repository', 'Service')}}} from '@/app/infrastructure/services/{directory_name}/{file_name}.service';")
impl_content.append("")
impl_content.append("@Injectable({")
impl_content.append("  providedIn: 'root'")
impl_content.append("})")
impl_content.append(f"export class {impl_class_name} implements {class_name} {{")
impl_content.append(f"  constructor(private primaryService: {class_name.replace('Repository', 'Service')}) {{")
impl_content.append("")
impl_content.append("  }")

for method in methods:
    # Extraer solo los nombres de los parámetros (sin tipos)
    param_names = []
    if method['params']:
        for param in method['params'].split(','):
            param_name = param.split(':')[0].strip()
            if param_name:
                param_names.append(param_name)

    params_call = ', '.join(param_names)

    impl_content.append(f"  async {method['name']}({method['params']}): Promise<{method['return_type']}> {{")
    impl_content.append(f"    return await this.primaryService.{method['name']}({params_call});")
    impl_content.append("  }")

impl_content.append("}")

# Escribir implementation repository
with open(infra_file, 'w') as f:
    f.write('\n'.join(impl_content))

print(f"✓ Archivos actualizados con {len(methods)} métodos")

