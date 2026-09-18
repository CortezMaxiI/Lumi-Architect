# Lumi Architect (AI Infrastructure Forge)

[![CI Pipeline](https://github.com/CortezMaxiI/Lumi-Architect/actions/workflows/ci.yml/badge.svg)](https://github.com/CortezMaxiI/Lumi-Architect/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-blue.svg)](https://microsoft.com/windows)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

## 1. Visión General y Misión Crítica
**Lumi Architect** es un sistema experto de orquestación de entornos de desarrollo asistido por Inteligencia Artificial. Su misión crítica es eliminar el trabajo manual, repetitivo y propenso a errores que conlleva el aprovisionamiento de entornos de desarrollo en Windows. El usuario ingresa un comando en lenguaje natural (ej. *"Configura un entorno MERN"* o *"Instala herramientas para Data Science"*), y el "Cerebro" del sistema deduce e infiere todas las dependencias necesarias. A partir de ello, genera un *Manifest* JSON estructurado que es validado e instalado silenciosamente utilizando el gestor de paquetes oficial de Windows (`winget`), asegurando instalaciones atómicas y limpias.

## 2. Arquitectura del Sistema y Flujo de Datos
El proyecto aplica una arquitectura **Neural-to-Script Pipeline**, dividida en capas funcionales independientes: Cognición (LLM), Control (API/CLI) y Ejecución (Forge).

```mermaid
flowchart TD
    UserInput["💬 Prompt (Lenguaje Natural)"] --> Brain["🧠 Capa Cognitiva (PromptEngine)"]
    Brain --> Manifest["📄 Manifiesto JSON"]
    Manifest --> Control["⚙️ Capa de Control (FastAPI / CLI)"]
    Control --> Validation["🔍 Validación de JSON Schema"]
    Validation --> Forge["🛠️ Capa de Ejecución (Forge - PowerShell)"]
    Forge --> Winget["📦 Gestor de Paquetes (Winget)"]
    Winget --> HealthCheck["🏥 Validación Post-Instalación (Health Check)"]
```

**Explicación del Flujo:**
1. El usuario interactúa a través de la CLI interactiva (`rich`) o la interfaz web React.
2. El string de lenguaje natural es enviado a la capa cognitiva (`Brain`), la cual consulta a un LLM configurado.
3. El LLM responde devolviendo un Manifiesto en formato JSON validado según `architecture_manifest.schema.json`.
4. El Manifiesto es transferido al `Forge` (scripts en PowerShell), que interroga al sistema para verificar qué software ya está instalado (Idempotencia).
5. Se ejecutan instalaciones silenciosas usando `winget install --silent --exact`.
6. Por último, `health_check.ps1` valida la disponibilidad de los ejecutables en el `PATH` de Windows.

## 3. Stack Tecnológico y Decisiones de Ingeniería
- **Motor Cognitivo y Backend API:** Python 3.11+ junto a FastAPI. Integra `LLMClient` multi-proveedor (Google Gemini, OpenAI / endpoints compatibles como Ollama) y un motor heurístico offline de contingencia.
- **Validación Estricta de Esquema:** `jsonschema` (Draft-7) actuando como compuerta de seguridad lógica. Ningún manifiesto llega al ejecutor sin pasar la validación formal de tipos, propiedades obligatorias y comprobación de idempotencia.
- **Interactividad CLI:** Librería `rich`. Añade retroalimentación de estado de alta calidad visual en la consola, como barras de progreso y renderizado condicional de tablas sin requerir frameworks pesados TUI.
- **Frontend Interfaz Web:** React 19 + Vite (`lumi-ui/`). Estilo visual Glassmorphism para exponer el orquestador a usuarios que prefieren dashboards web sobre consolas.
- **Ejecución Nativa:** PowerShell 7 + Winget. Winget es la fuente de verdad oficial de Microsoft para repositorios de software, asegurando que los paquetes instalados están firmados y libres de malware, superando a gestores de terceros como Chocolatey.

## 4. Componentes Clave y Análisis de Código
- `Lumi-Architect/brain/prompt_engine.py`: Encapsula la lógica de Chain-of-Thought (CoT) y la validación estricta contra el esquema JSON.
- `Lumi-Architect/brain/llm_client.py`: Capa de abstracción para proveedores de IA con fallback resiliente offline si no se configuran API keys.
- `Lumi-Architect/schemas/architecture_manifest.schema.json`: El contrato formal del sistema. Valida campos como `package_id`, `version_check_command`, `priority_level` y `is_critical`.
- `Lumi-Architect/forge/executor.ps1`: Motor de ejecución en PowerShell. Analiza el JSON, comprueba la existencia de cada `package_id` y delega la descarga/instalación a Winget evitando reinstalaciones.
- `Lumi-Architect/forge/health_check.ps1`: Verificación post-ejecución que comprueba la accesibilidad de cada binario en el PATH.
- `Lumi-Architect/main.py`: Punto de entrada de la CLI con manejo de terminal UTF-8, carga interactiva y feedback paso a paso.

## 5. Mapeo Teórico-Académico (Fundamentos de Ciencias de la Computación)
- **Compiladores y Autómatas (Validación Semántica):** Uso de Esquemas JSON como gramática formal libre de contexto para validar la salida (AST implícito) de la fase léxica generada por el LLM.
- **Sistemas Operativos e Infraestructura Inmutable:** Aplicación del principio de **Idempotencia**. Independientemente de la cantidad de veces que se ejecute el orquestador sobre un entorno, el estado final del sistema será idéntico al descripto en el Manifiesto.
- **Teoría de Agentes Reactivos:** El `PromptEngine` actúa como un agente de inferencia lógica de primer orden, mapeando una semántica informal (lenguaje humano) a reglas deterministas de máquina.

## 6. Guía de Despliegue y Configuración
### Requisitos Previos
- Windows 10/11 con `winget` habilitado (por defecto en builds modernos).
- Python 3.11+.
- Node.js v18+ (Solo para el dashboard web).

### Configuración del Entorno
1. Ejecutar el instalador automático de dependencias (instalará Python si no existe, creará el `.venv` e instalará dependencias):
```powershell
powershell -ExecutionPolicy Bypass -File setup_dependencies.ps1
```

2. *(Opcional)* Configurar variables de entorno:
```powershell
Copy-Item .env.example .env
# Editá .env y colocá tu GEMINI_API_KEY u OPENAI_API_KEY.
# Si lo dejás vacío, Lumi funciona perfectamente en modo inteligente offline.
```

### Ejecución de Pruebas Automatizadas
El proyecto cuenta con una suite integral de tests unitarios y de integración:
```powershell
.venv\Scripts\python.exe -m pytest tests/ -v
```

### Ejecución de la Aplicación
**Modo CLI Interactivo:**
```powershell
run.bat
# O directamente: .venv\Scripts\python.exe Lumi-Architect\main.py
```

**Modo Servidor Web / Dashboard:**
En la Terminal 1 (Backend FastAPI):
```powershell
.venv\Scripts\python.exe -m uvicorn Lumi-Architect.api:app --reload --port 8000
```
En la Terminal 2 (Frontend React):
```powershell
cd lumi-ui
npm run dev
```
