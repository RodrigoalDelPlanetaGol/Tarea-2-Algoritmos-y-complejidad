# Documentación
Este directorio contiene la implementación de la Tarea 2 de Algoritmos y Complejidad (INF221). La entrega está organizada en cuatro algoritmos (brute-force.cpp, dynamic-programming.cpp, greedy1.cpp y greedy2.cpp), un programa principal de medición (general.cpp), y dos scripts: uno para la generación de casos de prueba (testcases_generator.py) y otro para la generación de gráficos en base a las mediciones hechas (plot_generator.py)

## Implementación
El directorio 'algorithms/' contiene las cuatro implementaciones principales del problema. Cada archivo resuelve la misma tarea con una estrategia distinta: fuerza bruta, programación dinámica y dos variantes greedy (greedy1 prioriza satisfacción por minuto; greedy2 prioriza satisfacción por energía).

### Programa principal
El archivo 'general.cpp' ejecuta los cuatro algoritmos sobre los archivos de entrada ubicados en 'data/inputs/', genera los archivos de salida en 'data/outputs/' y registra las mediciones de tiempo y memoria en 'data/measurements/measurements.csv'.

### Scripts
El archivo 'scripts/testcases_generator.py' genera automáticamente los casos de prueba en 'data/inputs/' usando el formato pedido por el enunciado.

El archivo 'scripts/plot_generator.py' lee 'data/measurements/measurements'.csv y genera las gráficas del análisis experimental en 'data/plots/'.