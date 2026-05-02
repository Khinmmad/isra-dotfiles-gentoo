import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io

Item {
    id: sidebarRoot

    property bool open: false
    property var anchorItem: null
    signal closeRequested()

    // ── Datos del clima ──
    property string condition:  "—"
    property string tempC:      "—"
    property string feelsLike:  "—"
    property string humidity:   "—"
    property string windKmh:    "—"
    property string location:   "Cargando..."
    property var forecast:      []      // [{date, maxC, minC, desc}]
    property bool loading:      true

    function conditionEmoji(desc) {
        let d = (desc || "").toLowerCase();
        if (d.includes("thunder"))              return "⛈";
        if (d.includes("snow") || d.includes("blizzard")) return "❄️";
        if (d.includes("rain") || d.includes("drizzle")) return "🌧";
        if (d.includes("fog") || d.includes("mist"))     return "🌫";
        if (d.includes("overcast"))             return "☁️";
        if (d.includes("cloud") || d.includes("partly")) return "⛅";
        if (d.includes("sun") || d.includes("clear"))    return "☀️";
        if (d.includes("wind"))                 return "💨";
        return "🌤";
    }

    Process {
        id: weatherProc
        command: ["bash", "-c", "curl -sf --max-time 8 'wttr.in/?format=j1' 2>/dev/null"]
        stdout: StdioCollector { id: weatherOut }
        onExited: {
            sidebarRoot.loading = false;
            try {
                let data = JSON.parse(weatherOut.text.trim());
                let cur  = data.current_condition[0];
                let area = data.nearest_area[0];

                sidebarRoot.tempC     = cur.temp_C + "°C";
                sidebarRoot.feelsLike = cur.FeelsLikeC + "°C";
                sidebarRoot.humidity  = cur.humidity + "%";
                sidebarRoot.windKmh   = cur.windspeedKmph + " km/h";
                sidebarRoot.condition = cur.weatherDesc[0].value;
                sidebarRoot.location  = area.areaName[0].value
                                        + ", " + area.country[0].value;

                // Pronóstico 3 días
                let fc = [];
                for (let i = 0; i < Math.min(3, data.weather.length); i++) {
                    let w = data.weather[i];
                    fc.push({
                        date: w.date,
                        maxC: w.maxtempC,
                        minC: w.mintempC,
                        desc: w.hourly[4]?.weatherDesc[0]?.value ?? ""
                    });
                }
                sidebarRoot.forecast = fc;
            } catch(e) {
                sidebarRoot.condition = "Sin conexión";
                sidebarRoot.location  = "";
            }
        }
    }

    // Refrescar cada 10 minutos
    Timer {
        interval: 600000; running: true; repeat: true; triggeredOnStart: true
        onTriggered: { sidebarRoot.loading = true; weatherProc.running = true; }
    }

    // ── Control de animación de entrada/salida ──
    property bool popupShowing: false

    onOpenChanged: {
        if (open) {
            popupShowing = true;
        } else {
            slideOutTimer.start();
        }
    }

    Timer {
        id: slideOutTimer
        interval: 320
        onTriggered: sidebarRoot.popupShowing = false
    }

    // ── Popup principal ──
    PopupWindow {
        id: weatherPopup
        anchor.item: sidebarRoot.anchorItem
        anchor.edges: Edges.Left
        anchor.gravity: Edges.Left
        anchor.adjustment: PopupAdjustment.None
        implicitWidth: 280
        implicitHeight: 680
        visible: sidebarRoot.popupShowing
        color: "transparent"

        Rectangle {
            id: sidebarBg
            anchors.fill: parent
            color: "#1d1b09"
            border.color: "#514c1b"
            border.width: 1

            // Deslizamiento — entra desde la derecha
            property real slideProgress: (sidebarRoot.open && sidebarRoot.popupShowing) ? 0 : implicitWidth
            Behavior on slideProgress {
                NumberAnimation { duration: 320; easing.type: Easing.OutCubic }
            }
            transform: Translate { x: sidebarBg.slideProgress }
            opacity: sidebarRoot.open ? 1.0 : 0.6
            Behavior on opacity { NumberAnimation { duration: 200 } }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 14

                // ── Header ──
                RowLayout {
                    spacing: 8
                    Text {
                        text: "🌡 Clima"
                        color: "#f0c830"
                        font.pixelSize: 15; font.bold: true
                    }
                    Item { Layout.fillWidth: true }
                    // Refrescar
                    Rectangle {
                        width: 26; height: 26; radius: 13
                        color: refreshBtn.containsMouse ? "#514c1b" : "#2b2810"
                        Behavior on color { ColorAnimation { duration: 120 } }
                        Text {
                            anchors.centerIn: parent; text: "🔄"; font.pixelSize: 12
                            RotationAnimation on rotation {
                                id: spinAnim; from: 0; to: 360; duration: 800
                                running: sidebarRoot.loading
                                loops: Animation.Infinite
                            }
                        }
                        MouseArea {
                            id: refreshBtn; anchors.fill: parent; hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: { sidebarRoot.loading = true; weatherProc.running = true; }
                        }
                    }
                    // Cerrar
                    Rectangle {
                        width: 26; height: 26; radius: 13
                        color: closeBtn.containsMouse ? "#cc6e28" : "#2b2810"
                        Behavior on color { ColorAnimation { duration: 120 } }
                        Text { anchors.centerIn: parent; text: "✕"; font.pixelSize: 11; color: "#fef3c7" }
                        MouseArea {
                            id: closeBtn; anchors.fill: parent; hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: sidebarRoot.closeRequested()
                        }
                    }
                }

                // Ubicación
                Text {
                    text: "📍 " + sidebarRoot.location
                    color: "#9e8438"; font.pixelSize: 10
                    elide: Text.ElideRight; Layout.fillWidth: true
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: "#393616" }

                // ── Temperatura principal ──
                Rectangle {
                    Layout.fillWidth: true
                    height: 110; radius: 16
                    color: "#2b2810"
                    border.color: "#514c1b"; border.width: 1

                    ColumnLayout {
                        anchors.centerIn: parent; spacing: 4

                        Text {
                            text: sidebarRoot.conditionEmoji(sidebarRoot.condition)
                            font.pixelSize: 36
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Text {
                            text: sidebarRoot.tempC
                            color: "#f0c830"; font.pixelSize: 32; font.bold: true
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Text {
                            text: sidebarRoot.condition
                            color: "#ddc880"; font.pixelSize: 11
                            Layout.alignment: Qt.AlignHCenter
                            elide: Text.ElideRight
                        }
                    }
                }

                // ── Detalles ──
                GridLayout {
                    columns: 2; columnSpacing: 8; rowSpacing: 8
                    Layout.fillWidth: true

                    // Sensación térmica
                    Rectangle {
                        Layout.fillWidth: true; height: 44; radius: 10
                        color: "#2b2810"; border.color: "#393616"; border.width: 1
                        ColumnLayout {
                            anchors.centerIn: parent; spacing: 2
                            Text { text: "🌡 Sensación"; color: "#9e8438"; font.pixelSize: 9; Layout.alignment: Qt.AlignHCenter }
                            Text { text: sidebarRoot.feelsLike; color: "#fef3c7"; font.pixelSize: 14; font.bold: true; Layout.alignment: Qt.AlignHCenter }
                        }
                    }

                    // Humedad
                    Rectangle {
                        Layout.fillWidth: true; height: 44; radius: 10
                        color: "#2b2810"; border.color: "#393616"; border.width: 1
                        ColumnLayout {
                            anchors.centerIn: parent; spacing: 2
                            Text { text: "💧 Humedad"; color: "#9e8438"; font.pixelSize: 9; Layout.alignment: Qt.AlignHCenter }
                            Text { text: sidebarRoot.humidity; color: "#fef3c7"; font.pixelSize: 14; font.bold: true; Layout.alignment: Qt.AlignHCenter }
                        }
                    }

                    // Viento
                    Rectangle {
                        Layout.columnSpan: 2; Layout.fillWidth: true; height: 44; radius: 10
                        color: "#2b2810"; border.color: "#393616"; border.width: 1
                        RowLayout {
                            anchors.centerIn: parent; spacing: 8
                            Text { text: "💨 Viento"; color: "#9e8438"; font.pixelSize: 9 }
                            Text { text: sidebarRoot.windKmh; color: "#fef3c7"; font.pixelSize: 14; font.bold: true }
                        }
                    }
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: "#393616" }

                // ── Pronóstico 3 días ──
                Text {
                    text: "Próximos días"
                    color: "#9e8438"; font.pixelSize: 10; font.bold: true
                }

                Repeater {
                    model: sidebarRoot.forecast.length

                    Rectangle {
                        required property int index
                        property var day: sidebarRoot.forecast[index]
                        Layout.fillWidth: true; height: 44; radius: 10
                        color: "#2b2810"; border.color: "#393616"; border.width: 1

                        RowLayout {
                            anchors.fill: parent; anchors.margins: 10; spacing: 8

                            Text {
                                text: sidebarRoot.conditionEmoji(day.desc)
                                font.pixelSize: 18
                            }
                            Column {
                                spacing: 1
                                Text {
                                    text: Qt.formatDate(new Date(day.date), "ddd d MMM")
                                    color: "#fef3c7"; font.pixelSize: 11; font.bold: true
                                }
                                Text {
                                    text: day.desc
                                    color: "#9e8438"; font.pixelSize: 9
                                    elide: Text.ElideRight
                                    width: 120
                                }
                            }
                            Item { Layout.fillWidth: true }
                            Column {
                                spacing: 1; Layout.alignment: Qt.AlignVCenter
                                Text {
                                    text: day.maxC + "°"
                                    color: "#f0c830"; font.pixelSize: 13; font.bold: true
                                    anchors.right: parent.right
                                }
                                Text {
                                    text: day.minC + "°"
                                    color: "#9e8438"; font.pixelSize: 10
                                    anchors.right: parent.right
                                }
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                // Nota al pie
                Text {
                    text: "Datos: wttr.in"
                    color: "#514c1b"; font.pixelSize: 9
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
    }
}
