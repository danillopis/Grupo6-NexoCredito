# Datos y granos

Todos los CSV son UTF-8 con cabecera y separador coma. Los decimales físicos usan punto; los informes presentan formato español. No contienen datos de personas reales.

| Tabla | Grano | Claves y campos esenciales |
|---|---|---|
| historico | registro/partición | record_id único; partition train/reference/test_temporal; cohort; dti, utilization, prior_late, log_income; default_12m; ead |
| scoring | solicitud de monitorización | application_id único; cohort; canal principal; segmento; entradas; EAD; etiqueta madura; PD vigente y candidata; propuesta vigente |
| cartera | préstamo en un corte | loan_id único; stock_as_of=2025-06-30; cohorte de originación; saldo; atraso; improbable pago; saldo NPL |
| crm | mes-segmento-canal principal | activos iniciales, bajas, contactos, conversiones, gasto, tickets, resueltos en plazo, plantilla y formación del escenario |
| api | mes | solicitudes, éxitos y disponibilidad; P95/P99/frescura simulados, no mediciones del servidor de prueba |
| monitorizacion | cohorte vigente | tamaño, default, PD, AUC, KS, Brier, O/E, ECE, PSI y estado compuesto |
| politicas | cohorte-política | propuestas, aprobación, EAD, pérdidas esperadas/observadas y margen |
| segmentos | cohorte-modelo-tipo de grupo-grupo | desgloses por canal y segmento con tamaño y métricas |
| sensibilidad | cohorte-política-LGD-margen | los mismos resultados de políticas con LGD 25/45/65% y margen financiero 4/8/12% |

DTI significa servicio de deuda mensual / ingreso mensual. Utilización es saldo dispuesto / límite disponible. El atraso previo debe existir antes de la solicitud. La etiqueta de doce meses nunca entra en la predicción ni en la API. EAD se expresa en euros. El saldo NPL se define en la simulación por atraso superior a 90 días o improbable pago, asumiendo materialidad y sin modelar todas las reglas prudenciales.

En BI, Cohortes, Canales y Segmentos filtran hechos con relaciones uno-a-muchos unidireccionales. No unir directamente scoring con CRM o cartera para sumar importes. El grano y la fecha de cada tabla deben conservarse al interpretar filtros.
