📄 Software Requirements Specification (SRS)
Proyecto: Architect Lumi — AI Infrastructure Forge
Versión: 1.0
Estado: Finalizado para Desarrollo de MVP
Autor: [Tu Nombre/Antigravity]

1. Introducción
1.1 Propósito
Este documento define los requisitos técnicos y funcionales de Architect Lumi, un orquestador de infraestructura asistido por IA diseñado para automatizar la configuración de entornos de desarrollo en sistemas Windows mediante el uso de lenguaje natural.
1.2 Alcance del Sistema
Architect Lumi actúa como una capa de abstracción entre el desarrollador y el sistema operativo. Utiliza Modelos de Lenguaje de Gran Escala (LLM) para inferir dependencias técnicas y herramientas de gestión de paquetes (Winget/PowerShell) para la ejecución.

2. Descripción General
2.1 Perspectiva del Producto
Architect Lumi no es un instalador estático; es un sistema experto dinámico. A diferencia de herramientas como Ninite o scripts fijos de PowerShell, Lumi razona sobre las compatibilidades y herramientas necesarias para stacks tecnológicos específicos.
2.2 Funciones del Sistema
Interpretación de Contexto: Traducción de requisitos de usuario (ej. "Fullstack MERN") a un manifiesto técnico.
Resolución de Dependencias: Identificación de software base (Node.js, MongoDB) y herramientas auxiliares (Git, VS Code Extensions).
Ejecución Silenciosa: Instalación automatizada sin intervención del usuario.
Validación de Salud (Health Check): Verificación post-instalación de que los binarios están en el PATH y operativos.

3. Requerimientos Funcionales (RF)
ID
Requerimiento
Descripción
RF-01
Procesamiento de Lenguaje Natural (NLP)
El sistema debe interpretar prompts del usuario y extraer: Lenguajes, Motores de DB, e IDEs.
RF-02
Generación de Manifiesto JSON
La IA debe producir un objeto JSON estructurado con el esquema de versiones y nombres de paquetes compatibles con Winget.
RF-03
Orquestación de Winget/Choco
El sistema debe invocar el gestor de paquetes de Windows para realizar instalaciones -silent y --force.
RF-04
Configuración de Variables de Entorno
El sistema debe automatizar la adición de rutas al PATH del sistema si el instalador no lo hace.
RF-05
Pre-visualización del Plan (Dry Run)
El usuario debe poder ver y editar la lista de software antes de que comience la instalación.


4. Requerimientos No Funcionales (RNF)
ID
Atributo
Especificación
RNF-01
Seguridad (Safety Gate)
Ningún comando de sistema puede ejecutarse sin pasar por un filtro de "Comandos Permitidos" para evitar inyecciones maliciosas.
RNF-02
Idempotencia
Si una herramienta ya está instalada, el sistema debe detectarlo y omitirla sin lanzar errores.
RNF-03
Rendimiento
El tiempo de respuesta de la IA para generar el plan no debe superar los 5 segundos.
RNF-04
Interfaz (UI)
Estética High-Tech Dark Mode, consistente con la marca OptiMax/Lumi.


5. Arquitectura Técnica de Referencia
5.1 El "Neural-to-Script" Pipeline
User Input: Texto plano.
AI Orchestrator: LLM (GPT-4 / Claude 3) con un System Prompt especializado en ingeniería de software.
Bridge Layer: Script de Python que parsea el JSON y genera un archivo .ps1 (PowerShell) temporal.
OS Agent: Ejecutor con privilegios de Administrador que procesa el archivo .ps1.

6. Casos de Uso Clave
UC-01: Forja de Entorno Nuevo
Actor: Desarrollador.
Acción: El usuario solicita "Entorno para Data Science con Python".
Resultado: Lumi instala Python 3.10, Anaconda, VS Code, Jupyter Notebook y las extensiones de Python, configurando automáticamente los alias de terminal.
UC-02: Recuperación de Desastres
Actor: Desarrollador.
Acción: El usuario solicita "Reinstalar herramientas básicas de Git y Docker".
Resultado: El sistema verifica versiones actuales, actualiza o reinstala los binarios dañados.

7. Restricciones y Exclusiones
El sistema está limitado inicialmente a Windows 10/11.
No gestiona licencias de software de pago automáticamente.
Requiere conexión a internet para la descarga de paquetes y consulta al modelo de IA.

8. Criterios de Aceptación (Definición de Hecho)
El sistema puede configurar un entorno funcional de Node.js + Git en menos de 10 minutos (incluyendo descarga).
El usuario puede cancelar la operación en cualquier momento de forma segura.
El log de auditoría registra cada cambio realizado en el registro de Windows.
