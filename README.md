# Willkommen bei den WASM-basierten Jupyter-Notebooks von OWIDplus

Willkommen auf der WASM-basierten Jupyter-Notebook-Lösung von OWIDplus. 
OWIDplus ist eine Plattform für lexikalische Ressourcen des Leibniz-Institut für Deutsche Sprache (Mannheim). 
Die hier angebotenen Jupyter-Notebooks basieren auf der Technologie WebAssembly (WASM). 
Dabei werden Programmiersprachen wie beispielsweise Python oder R so übersetzt, dass sie direkt im Webbrowser ausgeführt werden können - 
ganz ohne zusätzliche lokale Installation.

Die bereitgestellten Jupyter-Notebooks sind vollständig interaktiv. 
Der enthaltene Code wird direkt in Ihrem Webbrowser ausgeführt. 
Sie können vorhandenen Code verändern, ergänzen oder auch eigene Notebooks laden und verwenden. 
Bitte beachten Sie, dass sämtliche Berechnungen und Verarbeitungen ausschließlich auf Ihrem eigenen Rechner stattfinden. 

Darüber hinaus ist zu bedenken, dass nur bestimmte Pakete und Bibliotheken bereits vorinstalliert sind. 
Weitere Informationen hierzu finden Sie im Abschnitt „Pakete / Technischer Hintergrund“.

# Kotakt / Rechtliche Hinweise

- Bei Fragen zu dieser Plattform wenden Sie sich bitte an: [Jan Oliver Rüdiger](https://perso.ids-mannheim.de/seiten/ruediger.html)
- [Datenschutzhinweis](https://www.owid.de/wb/owid/privacy.html)
- [Impressum](https://www.owid.de/wb/owid/impressum.html)

# Pakete / Technischer Hintergrund

Für die Ausführung der Python-Umgebung verwenden wir xeus-python in Version 13.3. 
Die folgenden Pakete sind bereits vorinstalliert und können direkt verwendet werden:

- ipycanvas
- numpy
- matplotlib
- lxml
- plotly
- plotly[express]
- pandas
- dayplot
- pydantic
- requests
- nbformat
- pyarrow
- wordcloud
- altair
- venn
- xlsxwriter
- pytest
- ipytest

Zusätzlich besteht die Möglichkeit, eigene Python-Packages zu installieren. 
Hierzu kann der Befehl `%pip install [package]` verwendet werden. 
Bitte berücksichtigen Sie dabei, dass ausschließlich Pakete funktionieren, die vollständig in Python implementiert sind. 
Pakete, die beispielsweise lediglich Wrapper für C- oder C++-Bibliotheken darstellen, können in der WASM-Umgebung nicht verwendet werden.

# Python- / R-Support

Python wird innerhalb der WASM-basierten Umgebung bereits sehr gut unterstützt und kann für viele typische Datenanalyse- und Verarbeitungsaufgaben 
problemlos eingesetzt werden. Der Support für R befindet sich derzeit hingegen noch in einem sehr experimentellen Stadium. 
Entsprechend kann es hierbei noch zu Einschränkungen oder Inkompatibilitäten kommen.

# Hinweis zu Daten

Wie bereits erwähnt, erfolgt die gesamte Verarbeitung direkt in Ihrem Webbrowser. 
Dateien, die durch Skripte oder Jupyter-Notebooks erzeugt oder verändert werden, werden ebenfalls direkt im Browser gespeichert. 
Diese Daten bleiben so lange erhalten, bis der Browser-Verlauf beziehungsweise der Browser-Cache gelöscht wird.
