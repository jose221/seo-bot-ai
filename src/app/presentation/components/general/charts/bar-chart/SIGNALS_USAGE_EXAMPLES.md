# 📘 Ejemplos de Uso con Signals

## ✅ Respuesta a tu pregunta: **SÍ, cambiará automáticamente**

Si le pasas un `signal` como input al componente `bar-chart`, **SÍ detectará los cambios automáticamente** gracias al `effect()` que implementamos.

---

## 🎯 Formas de usar el componente

### 1️⃣ **Con Signal (Recomendado - Reactivo Automático)**

```typescript
import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-dashboard',
  template: `
    <app-bar-chart 
      [items]="chartData()"
      [id]="'sales-chart'"
      [xKey]="'month'"
      [yKey]="'sales'"
    />
    
    <button (click)="updateData()">Actualizar Datos</button>
  `
})
export class DashboardComponent {
  // Signal con los datos
  chartData = signal([
    { month: 'Enero', sales: 1000 },
    { month: 'Febrero', sales: 1500 },
    { month: 'Marzo', sales: 1200 }
  ]);

  updateData() {
    // ✅ El gráfico se actualizará AUTOMÁTICAMENTE
    this.chartData.set([
      { month: 'Enero', sales: 2000 },
      { month: 'Febrero', sales: 2500 },
      { month: 'Marzo', sales: 2200 }
    ]);
  }
}
```

### 2️⃣ **Con Signal pasado directamente (También funciona)**

```typescript
import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-dashboard',
  template: `
    <app-bar-chart 
      [items]="chartData"
      [id]="'sales-chart'"
    />
  `
})
export class DashboardComponent {
  // Pasas el signal directamente (sin los paréntesis)
  chartData = signal([
    { label: 'Producto A', value: 100 },
    { label: 'Producto B', value: 200 }
  ]);

  ngOnInit() {
    // ✅ El componente detectará este cambio automáticamente
    setTimeout(() => {
      this.chartData.update(data => [
        ...data,
        { label: 'Producto C', value: 300 }
      ]);
    }, 2000);
  }
}
```

### 3️⃣ **Con Observable (Compatibilidad mantenida)**

```typescript
import { Component } from '@angular/core';
import { Observable } from 'rxjs';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-dashboard',
  template: `
    <app-bar-chart 
      [items]="chartData$"
      [id]="'api-chart'"
    />
  `
})
export class DashboardComponent {
  chartData$: Observable<any[]>;

  constructor(private http: HttpClient) {
    // ✅ También funciona con Observables
    this.chartData$ = this.http.get<any[]>('/api/chart-data');
  }
}
```

### 4️⃣ **Con Array estático**

```typescript
import { Component } from '@angular/core';

@Component({
  selector: 'app-dashboard',
  template: `
    <app-bar-chart 
      [items]="staticData"
      [id]="'static-chart'"
    />
  `
})
export class DashboardComponent {
  // ✅ Array estático también funciona
  staticData = [
    { label: 'Item 1', value: 50 },
    { label: 'Item 2', value: 75 }
  ];
}
```

---

## 🔥 Ejemplo Completo con DataSignalHelper

```typescript
import { Component, signal } from '@angular/core';
import { DataSignalHelper } from '@/app/helper/data-observable.helper';

@Component({
  selector: 'app-sales-dashboard',
  template: `
    <div class="dashboard">
      <h2>Dashboard de Ventas</h2>
      
      <!-- El gráfico se actualizará automáticamente -->
      <app-bar-chart 
        [items]="salesHelper.dataSignal"
        [id]="'sales-chart'"
        [xKey]="'month'"
        [yKey]="'amount'"
        [options]="chartOptions"
      />
      
      <button (click)="addSale()">Agregar Venta</button>
      <button (click)="refreshData()">Refrescar</button>
    </div>
  `
})
export class SalesDashboardComponent {
  // Usar el nuevo DataSignalHelper
  salesHelper = new DataSignalHelper<any[]>();
  
  chartOptions = {
    roundValue: 2,
    responsive: true,
    plugins: {
      legend: {
        display: true,
        position: 'top'
      }
    }
  };

  ngOnInit() {
    // Cargar datos iniciales
    this.loadInitialData();
    
    // Escuchar cambios automáticamente
    this.salesHelper.onChange((data) => {
      console.log('Datos actualizados:', data);
    });
  }

  loadInitialData() {
    const initialData = [
      { month: 'Enero', amount: 5000 },
      { month: 'Febrero', amount: 6000 },
      { month: 'Marzo', amount: 5500 }
    ];
    
    // ✅ Esto actualizará el gráfico automáticamente
    this.salesHelper.next(initialData);
  }

  addSale() {
    // ✅ Push automáticamente actualiza el gráfico
    this.salesHelper.push({ 
      month: 'Abril', 
      amount: 7000 
    });
  }

  refreshData() {
    // ✅ Update también actualiza automáticamente
    this.salesHelper.update((current: any) => 
      current.map((item: any) => ({
        ...item,
        amount: item.amount * 1.1 // Incrementar 10%
      }))
    );
  }
}
```

---

## 🎨 Ventajas de usar Signals

### ✅ **Reactividad automática**
```typescript
// Cambias el signal...
this.chartData.set(newData);
// ...y el gráfico se actualiza SOLO ✨
```

### ✅ **Sin subscripciones manuales**
```typescript
// ❌ ANTES (con Observables)
this.subscription = this.data$.subscribe(data => {
  this.updateChart(data);
});

// ✅ AHORA (con Signals)
chartData = signal(data); // ¡Eso es todo!
```

### ✅ **Sin memory leaks**
```typescript
// ❌ ANTES
ngOnDestroy() {
  this.subscription?.unsubscribe(); // Hay que recordar esto
}

// ✅ AHORA
// No necesitas ngOnDestroy, Angular limpia automáticamente
```

### ✅ **Performance mejorado**
```typescript
// Los signals usan OnPush automáticamente
// = Menos detecciones de cambios innecesarias
// = App más rápida 🚀
```

---

## 🔍 Cómo funciona internamente

El componente detecta si le pasaste un Signal y lo lee automáticamente:

```typescript
effect(() => {
  const itemsValue = this.items(); // Lee el input
  
  // Si es un Signal, lo ejecuta para leerlo
  if (this.isSignal(itemsValue)) {
    actualValue = itemsValue(); // ✅ Ahora es reactivo
  }
  
  // Actualiza el gráfico automáticamente
});
```

---

## 📝 Resumen

| Tipo de Input | ¿Cambia Automáticamente? | Recomendación |
|---------------|--------------------------|---------------|
| `signal(data)` pasado con `()` | ✅ SÍ | ⭐ Recomendado |
| Signal pasado directamente | ✅ SÍ | ⭐ Recomendado |
| Observable | ✅ SÍ | ✔️ Compatible |
| Array estático | ❌ NO (solo inicial) | ⚠️ Solo para datos fijos |

**Respuesta final:** **SÍ, si le pasas un Signal, el gráfico cambiará automáticamente cuando modifiques el signal.** 🎉

