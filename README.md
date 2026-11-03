# A.G.N.I.S-Agent

MVP de una cadena de agentes en Python para convertir un borrador de auditoría web y una plantilla institucional en un informe PDF.

## Estado del MVP

El pipeline ya separa:

1. **Normalización:** transforma el Markdown en un modelo Pydantic.
2. **POC:** usa un adaptador explícito; el adaptador incluido no ejecuta peticiones y deja los pasos sin confirmar.
3. **Clasificación:** propone vector CVSS 4.0, OWASP y causa técnica.
4. **Impacto:** recibe únicamente pasos confirmados.
5. **Renderizado:** el último componente rellena la plantilla DOCX o PDF y produce un PDF.

Las decisiones deterministas —confirmación de pasos, puntuación CVSS, severidad, tablas y validación final— todavía deben implementarse antes de usarlo en producción.

## Instalación

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[openai,dev]'
cp .env.example .env
```

Edita `.env` y añade tu clave:

```dotenv
OPENAI_API_KEY=tu_clave_de_openai
```

La aplicación carga automáticamente `.env` mediante `python-dotenv`. El archivo
`.env` está excluido de Git y nunca debe subirse al repositorio.

## Uso

```bash
agnis borrador.md plantilla.docx --output informe.pdf
```

También se aceptan plantillas PDF:

```bash
agnis borrador.md plantilla.pdf --output informe.pdf
```

Las plantillas usan marcadores `{{nombre}}`. Están disponibles `{{application}}`,
`{{base_url}}`, `{{environment}}`, `{{test_date}}`, `{{finding_count}}` y, para cada
hallazgo, `{{finding_1.title}}`, `{{finding_1.asset}}`, `{{finding_1.owasp}}`,
`{{finding_1.cause}}`, `{{finding_1.cwe}}`, `{{finding_1.cvss_vector}}`,
`{{finding_1.impact}}` y `{{finding_1.recommendations}}`.

Para DOCX se necesita LibreOffice instalado para convertir el documento final a PDF.
En PDF, los marcadores deben existir como texto seleccionable; A.G.N.I.S. los reemplaza
conservando la posición de la plantilla.

## Catálogo CWE

El workflow `Sync CWE catalog` descarga semanalmente el catálogo oficial
`cwec_v5.0.xml` desde MITRE y abre un pull request cuando detecta cambios. También
puede ejecutarse manualmente desde la pestaña **Actions**. El catálogo queda en
`data/cwec_v5.0.xml` y no se modifica directamente la rama `main`.

El modelo se configura mediante `langchain-openai` y usa `gpt-4o-mini` con temperatura cero. El proveedor está aislado en `agnis/llm.py` para poder sustituirlo sin modificar los agentes.

## Próximos adaptadores

- Implementar un `PocRunner` para navegador o Burp.
- Cargar `cwec_v5.0.xml` y filtrar candidatos antes del selector CWE.
- Calcular CVSS con la librería oficial y derivar la severidad en código.
- Añadir validación de esquema, persistencia de artefactos y revisión del auditor.
