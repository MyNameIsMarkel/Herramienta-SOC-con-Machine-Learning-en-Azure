# Herramienta SOC con Machine Learning (Análisis de tráfico + defensas) en Azure
SOC con Machine Learning en Microsoft Azure para la detección de tráfico anómalo y respuesta automática a incidentes de seguridad. Centraliza logs, entrena un modelo de ML para identificar comportamientos sospechosos y ejecuta defensas automáticas (bloqueo de IPs, reglas de firewall y playbooks) mediante SIEM/SOAR, sin intervención manual.

## Fase 1: Recolectar Datos
#### Paso 1: Habilitar fuentes de datos.
- Activar diagnósticos en Máquinas Virtuales (VM), Bases de Datos y Apps.
- Conectar los logs de red local o de otras nubes con Azure Arc.

#### Paso 2: Centralizar todo.
- Crear un Espacio de trabajo de Log Analytics. Donde llegan todos los registros.

## Fase 2: Machine Learning
#### Paso 3: Crear modelo de ML.
- Entrenar un modelo con tráfico normal para que aprenda qué es la "normalidad".

#### Paso 4: Publicar el modelo.
- Subir el modelo entrenado a un Endpoint para que otros servicios lo consulten.

## Fase 3: Defensas Automáticas
#### Paso 5: Configurar las defensas.
- Microsoft Sentinel (SIEM/SOAR). "Si el ML detecta un ataque X, ejecuta Y para defenderse".
- Azure Firewall / NSG. Negar accesos automáticamente.

## Fase 4: Automatización
#### Paso 6: Usar Azure Logic Apps o Sentinel Playbooks. Al recibir la orden, bloquea la IP del atacante en el firewall automáticamente, sin necesidad de tocar nada.


[========]


#Cálculo de costes
