# Grupo 6 | Nexo Crédito

Proyecto de Business Analytics, MLOps, CRM Balanced Scorecard y scoring crediticio. Entidad y datos completamente sintéticos.

Daniel Llopis Conejo — 225Q0111@live.uem.es  
Juan Sebastián Roman Herrera — 225S3293@live.uem.es  
Nicolás Rodríguez Oicatá — 225s3901@live.uem.es  
Andrés Fabricio Cabrera Torres — 225P5431@live.uem.es

## Leer los resultados

- Abrir `dashboard.html` directamente en un navegador. No necesita servidor ni conexión a internet.
- El proyecto Power BI está en `powerbi/NexoCredito.pbip`. Abrir con Power BI Desktop para Windows actualizado y pulsar **Actualizar** para cargar los datos integrados. Si Desktop solicita activar características de proyecto/PBIR, activarlas y reiniciar. No es un archivo PBIX y no debe renombrarse como tal.
- La página de políticas permite seleccionar junio, el holdout de contraste.
- `resultados/resumen.json`, `monitorizacion.csv`, `politicas.csv`, `segmentos.csv`, `sensibilidad.csv` y `calibracion.csv` contienen las cifras.

## Reproducir el experimento

Python 3.11 o posterior; el entorno verificado utiliza Python 3.12 y NumPy 2.3.5.

```text
python -m venv .venv
python -m pip install -r requirements-dev.txt
python src/experimento.py
python -m unittest discover -s tests -v
python src/generar_powerbi.py
python src/validar_powerbi.py
python src/generar_dashboard.py
```

Los scripts se ejecutan desde la carpeta del repositorio. El entrenamiento genera 8.000 registros de 2022, 2.500 de referencia, 2.500 de test temporal y 18.000 de monitorización. `historico.csv` y `scoring.csv` permiten inspeccionar las 31.000 observaciones. El generador utiliza semilla 6112026; el bootstrap, semilla 6112027. Las fechas son de origen; los resultados a doce meses son una reproducción histórica con etiquetas maduras a 18/11/2026.

La carpeta `validacion/esquemas/` contiene 13 esquemas públicos oficiales de Microsoft y su índice para validar PBIR sin acceso de red. Se han validado 32 documentos PBIR, nueve tablas, doce relaciones y las referencias de 24 visuales. Esta comprobación no ejecuta DAX, Power Query ni sustituye la apertura nativa en Desktop Windows.

## API y contención

```text
python src/api.py
```

API local en `http://127.0.0.1:8080`. GET `/health`; POST `/score` con este cuerpo:

```json
{"dti":0.32,"utilization":0.60,"prior_late":0,"monthly_income":2600}
```

El estado entregado de main contiene política 1.0.1 (contención) y modelo 1.0.0. El candidato 1.1.0 está disponible para validación, sin activarse automáticamente. Para ensayar el cambio:

```text
python src/activar_contencion.py --restaurar
python src/activar_contencion.py
```

`docs/CRISIS.md` describe incidente, roles y evidencias. No concede préstamos reales. No exponer esta API de demostración a internet: autenticación, TLS, límites y auditoría corporativos pertenecen al despliegue objetivo.

## Docker y CI/CD

```text
docker build -t nexo-scoring:grupo6 .
docker run --rm -p 127.0.0.1:8080:8080 nexo-scoring:grupo6
python src/smoke_http.py
```

La imagen base oficial de Python está fijada por digest. `.github/workflows/ci.yml` incluye generación, pruebas, validación BI, construcción de imagen y staging efímero para release/hotfix con la misma imagen. Configurar los revisores del entorno `staging` al publicar el repositorio. No se ha ejecutado GitHub Actions ni construido el contenedor local: Docker no estuvo disponible. Sí se verificaron los tests, los esquemas, los filtros HTML y 120 solicitudes HTTP locales. La latencia de loopback no es una certificación del SLA de producción.

## Git-Flow

Se adjunta `Grupo6_NexoCredito.bundle` en el paquete general. Para recuperar el repositorio con historial:

```text
git clone Grupo6_NexoCredito.bundle NexoCredito
git -C NexoCredito branch -a
git -C NexoCredito log --all --graph --oneline
```

Contiene main, develop, feature/modelo-interaccion, release/1.1.0, hotfix/1.0.1 y etiquetas v1.0.0/v1.0.1. El historial es una demostración técnica incluida en el proyecto; no acredita aportaciones individuales ni aprobaciones remotas.

## Supuestos que afectan a la interpretación

- El resultado de impago está disponible para todas las solicitudes solo porque es sintético; en producción existe sesgo de selección de concesión.
- El NPL es stock en un corte común; `default_12m` es incumplimiento acumulado por cohorte. No se intercambian.
- LGD 45%, EAD constante, margen 8% y coste 90 EUR son supuestos del escenario; no son NIIF 9 ni EBITDA bancario.
- La contención no repara coeficientes; el candidato reduce impago de propuestas y aprobación, con un coste de margen explícito.
- El uso de IA está declarado en la memoria. Las referencias docentes y regulatorias aparecen numeradas.
