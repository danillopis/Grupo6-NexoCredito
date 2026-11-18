# Grupo 6 | Ficha operativa de crisis

## Incidencia

En el replay histórico, al madurar las etiquetas de la cohorte de abril, O/E llega a 1,994 y Brier a 0,177. PSI es 0,0035 y AUC 0,861. La alerta no consiste en una caída de AUC. Los datos conservan un perfil similar, pero la relación entre endeudamiento, utilización e impago ha cambiado de forma no lineal.

## Reparto profesional

- Daniel Llopis Conejo: Business Owner. Cuantifica captación y margen que se sacrifican; no levanta límites de riesgo para sostener conversión.
- Juan Sebastián Roman Herrera: Data Scientist. Contrasta calidad, cambio de población y calibración; propone el candidato con interacción.
- Nicolás Rodríguez Oicatá: MLOps Engineer. Conserva versiones y evidencias; activa el hotfix de política, comprueba el servicio y prepara reversión.
- Andrés Fabricio Cabrera Torres: Risk Manager. Decide la contención, valida apetito y condiciones para promover el candidato.

## Decisiones y evidencias para ensayar

1. Abrir dashboard.html, MLOps y riesgo, cohorte abril. Identificar qué métricas fallan y cuáles no.
2. Mantener los coeficientes y la trazabilidad. Activar contención: `python src/activar_contencion.py`.
3. Comprobar que una solicitud con DTI 0,32 y utilización 0,60 pasa a revisión manual y conserva model_version 1.0.0, pero policy_version 1.0.1.
4. Comparar las tres políticas en junio. La contención reduce la concesión y no alcanza por sí sola el objetivo del 6% de impago acumulado entre propuestas. No se declara resuelta la crisis.
5. El candidato reduce el impago observado a 5,15%, a cambio de 6,37 puntos de aprobación y unos 15.361 EUR de margen respecto a la política vigente en esa cohorte. Es una decisión dentro de la simulación, no una ganancia de rentabilidad inventada.
6. La selección usa mayo; junio es contraste independiente. El resultado histórico no es una aprobación regulatoria, ni prueba un despliegue real en sombra.
7. Restaurar la configuración al terminar: `python src/activar_contencion.py --restaurar`.

## Disparador adicional para probar criterio profesional

Se comunica que las etiquetas de los últimos préstamos todavía no han madurado. En ese caso, no se calcula AUC ni se acusa al modelo de descalibración con resultados inexistentes. Se vigilan PSI, calidad, score, exposición y atrasos tempranos como señales, manteniendo pendientes las métricas a doce meses.

Esta ficha prepara las decisiones y acciones de la simulación. El guion audiovisual, reparto de tiempos y diapositivas se elaborarán en la siguiente fase.
