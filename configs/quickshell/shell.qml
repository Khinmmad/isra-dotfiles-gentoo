import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland

ShellRoot {

    // ══════════════════════════════════════
    //  BARRA SUPERIOR — ancho completo
    // ══════════════════════════════════════
    PanelWindow {
        id: topPanel
        anchors { top: true; left: true; right: true; bottom: false }
        margins { top: 0; left: 0; right: 0 }
        implicitHeight: 48
        color: "transparent"

        Rectangle {
            id: panelRect
            anchors.fill: parent
            color: "#1d1b09"

            // Borde inferior que conecta visualmente con las barras laterales
            Rectangle {
                anchors.left: parent.left; anchors.right: parent.right
                anchors.bottom: parent.bottom; height: 1
                color: "#514c1b"
            }

            scale: 0.98; opacity: 0.0
            Component.onCompleted: { scale = 1.0; opacity = 1.0 }
            Behavior on scale   { NumberAnimation { duration: 400; easing.type: Easing.OutBack } }
            Behavior on opacity { NumberAnimation { duration: 300; easing.type: Easing.OutSine } }

            RowLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 20

                // Logo / menú
                Rectangle {
                    id: logoContainer
                    Layout.alignment: Qt.AlignVCenter
                    Layout.leftMargin: 6
                    width: 32; height: 32; radius: 16
                    color: logoArea.containsMouse ? "#514c1b" : "#393616"
                    Behavior on color { ColorAnimation { duration: 150 } }
                    Text { anchors.centerIn: parent; text: "🐻"; font.pixelSize: 16 }
                    MouseArea {
                        id: logoArea; anchors.fill: parent
                        hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                        onClicked: appMenu.toggle()
                    }
                }

                Workspaces { Layout.alignment: Qt.AlignVCenter }

                Item { Layout.fillWidth: true }

                NetworkStatus { Layout.alignment: Qt.AlignVCenter }

                Item {
                    width: 16; height: 32; Layout.alignment: Qt.AlignVCenter
                    Rectangle { anchors.centerIn: parent; width: 1; height: 16; color: "#514c1b" }
                }

                SystemInfo { Layout.alignment: Qt.AlignVCenter }
                Music       { Layout.alignment: Qt.AlignVCenter }
                BarClock    { Layout.alignment: Qt.AlignVCenter }
            }

            Launcher { id: appMenu; anchorItem: logoContainer }
        }
    }

    // ══════════════════════════════════════
    //  BARRA IZQUIERDA — borde izquierdo
    // ══════════════════════════════════════
    PanelWindow {
        anchors { left: true; top: true; bottom: true; right: false }
        margins { top: 48; bottom: 0; left: 0 }
        implicitWidth: 6
        color: "transparent"

        Rectangle {
            anchors.fill: parent
            color: "#1d1b09"
            // Línea de borde derecha (visual, hacia el interior)
            Rectangle {
                anchors.right: parent.right; anchors.top: parent.top; anchors.bottom: parent.bottom
                width: 1; color: "#514c1b"
            }
        }
    }

    // ══════════════════════════════════════
    //  BARRA DERECHA — panel clima + borde
    // ══════════════════════════════════════
    PanelWindow {
        id: rightPanel
        anchors { right: true; top: true; bottom: true; left: false }
        margins { top: 48; bottom: 0; right: 0 }
        implicitWidth: 48
        color: "transparent"

        property bool weatherOpen: false

        Rectangle {
            id: rightPanelRect
            anchors.fill: parent
            color: "#1d1b09"

            // Línea de borde izquierda
            Rectangle {
                anchors.left: parent.left; anchors.top: parent.top; anchors.bottom: parent.bottom
                width: 1; color: "#514c1b"
            }

            Column {
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
                anchors.topMargin: 16
                spacing: 20

                // Botón para abrir/cerrar sidebar de clima
                Rectangle {
                    width: 36; height: 36; radius: 18
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: weatherBtn.containsMouse
                        ? "#514c1b"
                        : (rightPanel.weatherOpen ? "#393616" : "#2b2810")
                    Behavior on color { ColorAnimation { duration: 150 } }
                    scale: weatherBtn.pressed ? 0.9 : (weatherBtn.containsMouse ? 1.1 : 1.0)
                    Behavior on scale { NumberAnimation { duration: 100; easing.type: Easing.OutBack } }

                    Text {
                        anchors.centerIn: parent
                        text: "🌤"
                        font.pixelSize: 17
                    }

                    // Indicador activo
                    Rectangle {
                        visible: rightPanel.weatherOpen
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: -6
                        width: 4; height: 4; radius: 2
                        color: "#f0c830"
                    }

                    MouseArea {
                        id: weatherBtn; anchors.fill: parent
                        hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                        onClicked: rightPanel.weatherOpen = !rightPanel.weatherOpen
                    }
                }
            }

            // Sidebar de clima (PopupWindow que se desliza desde la derecha)
            WeatherSidebar {
                id: weatherSidebar
                anchorItem: rightPanelRect
                open: rightPanel.weatherOpen
                onCloseRequested: rightPanel.weatherOpen = false
            }
        }
    }

    // ══════════════════════════════════════
    //  BARRA INFERIOR — borde inferior
    // ══════════════════════════════════════
    PanelWindow {
        anchors { bottom: true; left: true; right: true; top: false }
        margins { bottom: 0; left: 6; right: 48 }
        implicitHeight: 6
        color: "transparent"

        Rectangle {
            anchors.fill: parent
            color: "#1d1b09"
            // Línea de borde superior
            Rectangle {
                anchors.left: parent.left; anchors.right: parent.right
                anchors.top: parent.top; height: 1
                color: "#514c1b"
            }
        }
    }
}
