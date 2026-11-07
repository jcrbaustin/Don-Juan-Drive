# Constitución Estricta: Anti-Broken Buttons y Optimización de Tokens (RSC)

## 1. Prohibición Total de Elementos UI "Vacíos"
- Prohibido generar botones, inputs, modales o formularios sin un handler real y funcional conectado.
- Prohibido terminantemente: `onClick={() => {}}`, `onClick={() => console.log('...')}`, `// TODO: implement`, o alertas temporales.
- Invariante: Si la función, mutación, hook o endpoint backend NO existe todavía, NO RENDERICES el elemento visual en la interfaz.

## 2. Orden de Ejecución Obligatorio (Lógica Antes que Vista)
- **Paso 1**: Definir tipos, contratos de datos, estado y funciones/APIs correspondientes.
- **Paso 2**: Implementar y validar los handlers.
- **Paso 3**: Maquetar el componente visual y conectar los handlers ya existentes del Paso 2.

## 3. Optimización Máxima de Tokens
- No saludes, no repitas explicaciones teóricas ni dupliques código que no ha cambiado.
- Entrega únicamente diffs, archivos finales o comandos concretos.
- Si una tarea es amplia, implementa únicamente las funciones acordadas en el alcance actual sin maquetar secciones a medias.
- Activa el ciclo estricto: Plan (Dry-Run de 3 puntos: Estado -> Handlers -> UI) -> Implement -> Review.
