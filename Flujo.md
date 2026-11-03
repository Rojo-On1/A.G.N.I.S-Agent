# Flujo de A.G.N.I.S

A.G.N.I.S. convierte un borrador de auditoría en un informe estructurado mediante agentes especializados y código determinista. El flujo no permite que un agente decida condiciones de negocio, confirme resultados, calcule severidades o incorpore datos que no reciba.

## Flujo canónico

```text
Borrador Markdown original (inmutable)
        |
        v
Normalizador
  - estructura el texto
  - conserva literalmente las acciones
  - marca datos faltantes y ambigüedades
        |
        v
Revisión del auditor de la normalización
        |
        v
Parser / Splitter (código)
  - valida el esquema
  - separa un paquete por hallazgo
  - asigna la sección WSTG según la ubicación del hallazgo
  - calcula exposición y privilegio a partir de los datos estructurados
        |
        +------------------------------+
        |                              |
        v                              v
POC por hallazgo                 Clasificación técnica
  - ejecuta pasos literales       - propone vector CVSS 4.0
  - registra observaciones        - propone OWASP
  - guarda la captura final       - propone causa técnica
        |                              |
        v                              v
Filtro de confirmación (código)  Catálogo CWE local
  - compara observado/esperado     - busca candidatos en cwec_v5.0.xml
  - no interpreta ni redacta        - entrega candidatos al clasificador
  - produce pasos confirmados       - el clasificador elige un CWE válido
        |                              |
        +------------------------------+
                       |
                       v
Impacto y recomendaciones
  - recibe solo pasos confirmados
  - describe únicamente lo demostrado
  - recomienda controles aplicables
                       |
                       v
Resolución (código)
  - calcula la puntuación CVSS con la librería
  - deriva la severidad de la puntuación
  - genera tablas, conteos y prioridades
  - genera frases de conclusión mediante reglas
  - resuelve referencias y campos de plantilla
                       |
                       v
Redactor
  - copia los datos resueltos
  - ensambla el Markdown institucional
  - no calcula ni clasifica
                       |
                       v
Validador del informe (código)
  - comprueba esquema, referencias, cobertura y placeholders
  - bloquea la salida si faltan datos obligatorios
                       |
                       v
Revisión final del auditor
                       |
                       v
Informe final A.G.N.I.S.
```

## Reglas de separación

### El borrador y sus versiones

Se conservan tres artefactos distintos:

1. **Borrador original:** texto recibido, inmutable y trazable.
2. **Borrador normalizado:** estructura propuesta por el Normalizador, con pendientes y ambigüedades.
3. **Datos resueltos:** resultados de ejecución, clasificación confirmada y valores calculados que consume el Redactor.

Los agentes reciben la versión mínima necesaria. No se envía el documento completo a todos los agentes.

### Decisiones del código

El código, no los agentes, debe:

- validar esquemas y datos obligatorios;
- separar hallazgos y pasos;
- comparar resultados observados con resultados esperados;
- decidir qué pasos quedan confirmados;
- calcular la puntuación CVSS con `CVSS4`;
- derivar la severidad desde la puntuación;
- consultar `cwec_v5.0.xml` y validar el identificador elegido;
- generar conteos, tablas, prioridades y frases regladas;
- impedir que placeholders o datos faltantes lleguen al informe final.

Los agentes solo producen propuestas u observaciones dentro de su contrato.

## Contratos de los agentes

### Normalizador

Entrada: un Markdown original.

Salida: datos generales, secciones WSTG, hallazgos, pasos literales, pendientes, ambigüedades y asignaciones propuestas. No inventa resultados esperados, cuentas, severidades ni impacto.

### POC

Entrada: un único paquete de hallazgo con alcance, cuentas y pasos.

Salida: resultado observado por paso, apuntes, brechas, entidades creadas y una captura del último paso. No compara con el resultado esperado ni concluye si el hallazgo existe.

### Clasificador técnico

Entrada: título, causa descrita, pasos y metadatos de exposición y privilegio.

Salida: vector CVSS 4.0 propuesto, categoría OWASP válida y causa técnica. La puntuación y la severidad no las produce el agente.

### Selector CWE

Entrada: causa técnica y candidatos extraídos por código del catálogo oficial.

Salida: un CWE existente del conjunto de candidatos, o una marca explícita para revisión del auditor. No inventa identificadores.

### Impacto y recomendaciones

Entrada: pasos confirmados, resultados observados confirmados y categoría WSTG.

Salida: impacto demostrado, con referencia al paso, y recomendaciones con su fuente. No recibe ni usa observaciones no confirmadas.

### Redactor

Entrada: objeto final resuelto por código.

Salida: informe Markdown con la plantilla institucional. Copia los valores recibidos y escribe únicamente las frases de enlace definidas por su contrato.

## Puntos de control humano

El auditor conserva la autoridad en dos momentos:

1. **Después de la normalización:** confirma estructura, categorías WSTG, cuentas y pendientes.
2. **Antes de publicar:** revisa resultados confirmados, clasificación, impacto, recomendaciones y el informe ensamblado.

Una revalidación completa del POC después de redactar no forma parte del flujo normal: el informe se redacta exclusivamente a partir de los datos ya confirmados. Si cambia un paso, una cuenta, un endpoint o el resultado esperado, el código invalida los resultados derivados y vuelve a ejecutar el hallazgo afectado.

## Reglas de invalidez y repetición

- Si cambia el borrador original, se crea una nueva ejecución del flujo.
- Si cambia la normalización, se invalidan los paquetes derivados de ese hallazgo.
- Si cambia un paso o su resultado esperado, se repite el POC y el filtro de confirmación.
- Si cambia la clasificación, se recalculan CVSS, severidad, tablas y prioridades.
- Si cambia el impacto o las recomendaciones, solo se vuelve a ejecutar la validación del informe.

Cada ejecución debe conservar identificadores de versión para mantener la trazabilidad entre entrada, observaciones, decisiones y salida.

## Pendientes de implementación

1. Definir los esquemas JSON y sus validadores.
2. Implementar el Parser / Splitter y el filtro de confirmación.
3. Implementar la consulta de `cwec_v5.0.xml` y la validación del CWE elegido.
4. Implementar el resolvedor de CVSS, severidad, tablas, prioridades y conclusiones.
5. Definir los textos fijos de confidencialidad y glosario.
6. Definir el origen de la descripción de cada hallazgo; por defecto debe ser un campo explícito del auditor y no una inferencia del modelo.
7. Implementar el validador final y los estados de revisión.
8. Ejecutar una prueba piloto completa con un hallazgo real de la plantilla institucional.
