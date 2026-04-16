import json
from app.services.schema_validators import SchemaValidatorPipeline

pipeline = SchemaValidatorPipeline()

# Test 1: Recipe sin image (Google lo requiere)
print('=== Test 1: Recipe sin image ===')
data = {
    "@context": "https://schema.org",
    "@type": "Recipe",
    "name": "Classic Omelette",
}
result = pipeline.run(data, "test")
print(json.dumps(result, indent=2, ensure_ascii=False))

# Test 2: FAQPage con preguntas incompletas
print("\n=== Test 2: FAQPage incompleta ===")
faq = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
        {"@type": "Question", "name": "Pregunta 1"},
        {"@type": "Question", "name": "Pregunta 2", "acceptedAnswer": {"@type": "Answer", "text": "Respuesta 2"}},
    ]
}
result2 = pipeline.run(faq, "test-faq")
print(json.dumps(result2, indent=2, ensure_ascii=False))

# Test 3: Product completo
print("\n=== Test 3: Product con offers ===")
product = {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "Widget",
    "image": "https://example.com/photo.jpg",
    "offers": {
        "@type": "Offer",
        "price": "19.99",
        "priceCurrency": "USD",
        "availability": "https://schema.org/InStock",
    }
}
result3 = pipeline.run(product, "test-product")
print(json.dumps(result3, indent=2, ensure_ascii=False))

# Test 4: JSON-LD con contexto invalido
print("\n=== Test 4: JSON-LD contexto invalido ===")
broken = {"@context": "invalid-context", "@type": "Recipe", "name": "Test"}
result4 = pipeline.run(broken, "broken")
print(json.dumps(result4, indent=2, ensure_ascii=False))

# Test 5: Integrado via SchemaAuditService
print("\n=== Test 5: SchemaAuditService integrado ===")
from app.services.schema_audit_service import get_schema_audit_service
svc = get_schema_audit_service()
full_result = svc.validate_schema_payload(data, "recipe-test")
print(json.dumps(full_result, indent=2, ensure_ascii=False))

print("\n✅ Todos los tests pasaron")

