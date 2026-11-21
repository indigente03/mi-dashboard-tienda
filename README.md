# 🏪 Dashboard de Ventas e Inventario para Tienda de Barrio

##  Descripción del Proyecto
Este proyecto consiste en el desarrollo de un dashboard interactivo y de código abierto para la gestión de ventas e inventario de una tienda de barrio colombiana. Fue desarrollado como parte del trabajo de grado enfocado en demostrar que es posible implementar soluciones de Business Intelligence (BI) ligeras y eficientes utilizando **Streamlit**, **Plotly** y el estándar **HTML**, como alternativa a plataformas tradicionales como Power BI o Tableau.

La solución busca reducir la huella de infraestructura (servidores más pequeños y menor consumo de recursos), alineándose con los Objetivos de Desarrollo Sostenible (ODS 6 y 9) y democratizando el acceso a la analítica de datos para las PYMES.

## Características Principales
- **Módulo de Ventas**: KPIs de rendimiento (ventas totales, ticket promedio), gráficos de ventas por mes, top de productos más vendidos, acumulado de ventas y análisis de ventas por día de la semana.
- **Módulo de Inventario**: Alertas de stock (crítico, bajo, ok), valorización del inventario, gráfico de stock vs. mínimo y análisis de rotación de productos.
- **Filtros Interactivos**: Selector de meses con `st.segmented_control` y filtros por categoría.
- **Procesamiento Eficiente**: Carga de datos desde archivos CSV locales sin requerir motores de bases de datos pesados.

##  Tecnologías Utilizadas
- [Python 3.10+](https://www.python.org/)
- [Streamlit](https://streamlit.io/) - Framework para aplicaciones web de datos.
- [Pandas](https://pandas.pydata.org/) - Manipulación y análisis de datos.
- [Plotly](https://plotly.com/python/) - Visualizaciones interactivas.

##  Estructura del Proyecto
```text
mi-dashboard-tienda/
│
├── app.py                  # Código principal de la aplicación Streamlit
├── requirements.txt        # Dependencias del proyecto
├── .gitignore              # Archivos ignorados por Git
├── README.md               # Documentación del proyecto
│
├── data/                   # Archivos CSV con datos simulados (2026)
│   ├── productos.csv
│   ├── inventario.csv
│   ├── ventas_cabecera.csv
│   └── ventas_detalle.csv
│
└── assets/                 # Recursos estáticos
    └── imagenes/           # Logos e imágenes para el dashboard
