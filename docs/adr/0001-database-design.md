# ADR 0001: Diseño del Esquema de Base de Datos para Gestión de Cartera

**Estado:** Aceptado
**Fecha:** 24 de febrero de 2026

## 1. Contexto

Para el módulo de gestión de créditos de consumo, necesitamos un esquema de base de datos relacional que garantice consistencia financiera y cumpla con las normativas locales colombianas.

## 2. Decisiones de Diseño y Justificación

### A. Tipos de dato para el dinero: `NUMERIC(18, 2)`

Decidí descartar por completo el uso de `FLOAT` o `REAL` para cualquier campo que represente dinero o tasas. En la práctica, la aritmética de punto flotante genera problemas de redondeo.

Opté por `NUMERIC(18, 2)` para los montos en pesos colombianos (COP). A nivel de causación de intereses diarios es obligatorio mantener esa precisión. El tamaño 18 nos da margen de sobra para manejar carteras gigantes y consolidación de balances sin riesgo de desbordamiento (overflow).

Para las tasas de interés, usé `NUMERIC(10, 6)` para asegurar exactitud matemática al convertir tasas (ej. de Efectiva Anual a Nominal Mes Vencido).

### B. Separación estricta entre el "Pago" y su "Aplicación"

En lugar de tener una sola tabla que registre que un cliente pagó X cantidad, dividí esto en dos: `payments` (el evento del pago entrante) y `payment_allocations` (el desglose interno).

**¿Por qué?** En Colombia, la ley dicta un orden estricto de prelación de pagos (costas judiciales -> seguros -> intereses de mora -> intereses corrientes -> capital). Cuando entran $100.000 COP, el dominio de la aplicación debe calcular cómo se reparte esa plata. Esta separación nos permite auditar exactamente a qué rubros se fue cada peso de un abono.

### C. Idempotencia desde la base de datos

Agregué un constraint `UNIQUE` al campo `payment_reference` en la tabla de pagos.

Sabiendo que nos vamos a integrar con pasarelas como PSE o recaudo bancario, es súper común que los webhooks fallen por red o se envíen por duplicado, aplicando previamente un _bloqueo optimista_ a traves de un ID y un estado (procesando), si llega el mismo ID de transacción dos veces, el motor lo rechaza y evitamos duplicar un pago por error.

### D. Registro Contable "Append-Only" (Libro Mayor)

Para el registro contable (`journal_entries` y `journal_entry_lines`), apliqué el principio de partida doble. Estas tablas están diseñadas para ser de solo inserción (append-only).

Aquí no hacemos `UPDATE` para corregir un saldo; si hay un error, el sistema debe generar un nuevo asiento contable de reversión.
