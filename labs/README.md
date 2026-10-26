# Laboratorios de Ciencia de Datos

## Entregas

| Semana / sesión | Contenido | Acceso |
| --- | --- | --- |
| Semana 07 | Laboratorio integrador I, conservado sin cambios | [Carpeta](semana-07/laboratorio-integrador-i/) |
| Semana 09, sesión 02 | Ejercicio 2: pipeline completo de features | [Código](semana-09-sesion-02/starter/ejercicio2_pipeline.py) · [Respuestas](semana-09-sesion-02/README.md#ejercicio-2-el-pipeline-completo) |
| Semana 10, sesión 01 | Ejercicio 2: regularización y comparación de modelos | [Código](semana-10-sesion-01/starter/ejercicio2_regularizacion.py) · [Respuestas](semana-10-sesion-01/README.md#ejercicio-2-regularizar-una-regresión-que-se-sobreajusta) · [Resultados CSV](semana-10-sesion-01/starter/resultados_ejercicio2.csv) |

En las dos sesiones nuevas se completó el **ejercicio 2** y sus respuestas en el README. Los ejercicios 1 y las plantillas de otros ejercicios se conservan como referencia del material original; no se presentan como ejercicios resueltos.

## Ejecutar los ejercicios 2

Desde la raíz del repositorio, con Python 3.11 y las dependencias del curso:

```bash
python -m pip install -r labs/requirements.txt
```

Semana 09, sesión 02:

```bash
cd labs/semana-09-sesion-02/starter
python ejercicio2_pipeline.py
```

Semana 10, sesión 01 (desde la raíz del repositorio):

```bash
cd labs/semana-10-sesion-01/starter
python ejercicio2_regularizacion.py
```

Cada script utiliza su `viajes_features.csv`, incluido junto al código. El segundo genera `resultados_ejercicio2.csv`.

## Validación

- Semana 09: las cinco comprobaciones originales imprimen `TODO 1: OK` hasta `TODO 5: OK`. Produce 25 columnas, con 2380 filas de entrenamiento y 595 de prueba.
- Semana 10: las cinco comprobaciones originales imprimen `Paso 1: OK` hasta `Paso 5: OK`. Gradient Boosting logra un MAE de prueba de 1.2754 frente a 12.5308 de la línea base.
- Validado en Windows con Python 3.12 y las versiones de NumPy, pandas y scikit-learn fijadas en `requirements.txt`. El entorno del curso usa Python 3.11. El error extremo de la regresión sin regularizar y los tiempos pueden variar según la plataforma y las bibliotecas numéricas.

Material base: [ErickNaunay/data-science-end-to-end](https://github.com/ErickNaunay/data-science-end-to-end), commit `f9c474b`. Se conserva su [licencia MIT](LICENSE-material-curso.txt).
