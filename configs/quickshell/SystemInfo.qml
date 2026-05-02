import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io

Item {
    id: sysRoot
    implicitWidth: sysRow.implicitWidth
    implicitHeight: sysRow.implicitHeight

    property bool barHovered: sysHover.containsMouse
    property bool popupHovered: false
    property bool anyHovered: barHovered || popupHovered
    property bool popupVisible: false

    onAnyHoveredChanged: {
        if (anyHovered) { hideTimer.stop(); showTimer.start() }
        else            { showTimer.stop(); hideTimer.start() }
    }

    Timer { id: showTimer; interval: 200; onTriggered: sysRoot.popupVisible = true }
    Timer { id: hideTimer; interval: 500; onTriggered: if (!sysRoot.anyHovered) sysRoot.popupVisible = false }

    RowLayout {
        id: sysRow
        spacing: 10

        // CPU
        Rectangle {
            Layout.alignment: Qt.AlignVCenter
            height: 32; width: cpuText.implicitWidth + 20
            radius: 16; color: "#2b2810"
            border.color: "#514c1b"; border.width: 1
            Text {
                id: cpuText
                anchors.centerIn: parent
                text: "⚙️ --%"
                color: "#ff8c42"
                font.pixelSize: 13; font.bold: true
            }
        }

        // RAM
        Rectangle {
            Layout.alignment: Qt.AlignVCenter
            height: 32; width: ramText.implicitWidth + 20
            radius: 16; color: "#2b2810"
            border.color: "#514c1b"; border.width: 1
            Text {
                id: ramText
                anchors.centerIn: parent
                text: "🧠 --%"
                color: "#c8e882"
                font.pixelSize: 13; font.bold: true
            }
        }
    }

    MouseArea { id: sysHover; anchors.fill: sysRow; hoverEnabled: true }

    PopupWindow {
        id: sysPopup
        anchor.item: sysRoot
        anchor.edges: Edges.Bottom; anchor.gravity: Edges.Bottom
        anchor.adjustment: PopupAdjustment.Slide
        implicitWidth: 200; implicitHeight: 130
        visible: sysRoot.popupVisible
        color: "transparent"

        Rectangle {
            width: 200; height: 130
            color: "#1d1b09"; radius: 20
            border.color: "#514c1b"; border.width: 1

            opacity: sysRoot.popupVisible ? 1.0 : 0.0
            scale:   sysRoot.popupVisible ? 1.0 : 0.95
            Behavior on opacity { NumberAnimation { duration: 200 } }
            Behavior on scale   { NumberAnimation { duration: 250; easing.type: Easing.OutBack } }

            MouseArea {
                anchors.fill: parent; hoverEnabled: true
                onContainsMouseChanged: sysRoot.popupHovered = containsMouse
            }

            ColumnLayout {
                anchors.fill: parent; anchors.margins: 16; spacing: 12

                Text {
                    text: "Estado del Sistema"
                    color: "#fef3c7"; font.pixelSize: 14; font.bold: true
                    Layout.alignment: Qt.AlignHCenter
                }

                ColumnLayout {
                    spacing: 4
                    RowLayout {
                        Text { text: "CPU";    color: "#cc6e28"; font.pixelSize: 11; font.bold: true }
                        Item { Layout.fillWidth: true }
                        Text { text: cpuText.text.split(" ")[1]; color: "#ddc880"; font.pixelSize: 11 }
                    }
                    Rectangle {
                        Layout.fillWidth: true; height: 6; radius: 3; color: "#393616"
                        Rectangle {
                            height: parent.height; radius: 3
                            width: parent.width * (parseFloat(cpuText.text.split(" ")[1]) / 100)
                            color: "#cc6e28"
                            Behavior on width { NumberAnimation { duration: 500 } }
                        }
                    }
                }

                ColumnLayout {
                    spacing: 4
                    RowLayout {
                        Text { text: "Memoria"; color: "#96c836"; font.pixelSize: 11; font.bold: true }
                        Item { Layout.fillWidth: true }
                        Text { text: ramText.text.split(" ")[1]; color: "#ddc880"; font.pixelSize: 11 }
                    }
                    Rectangle {
                        Layout.fillWidth: true; height: 6; radius: 3; color: "#393616"
                        Rectangle {
                            height: parent.height; radius: 3
                            width: parent.width * (parseFloat(ramText.text.split(" ")[1]) / 100)
                            color: "#96c836"
                            Behavior on width { NumberAnimation { duration: 500 } }
                        }
                    }
                }
            }
        }
    }

    Process {
        id: ramProc
        command: ["bash", "-c", "free -m | awk '/^Mem/ {printf \"%.0f\", $3/$2 * 100}'"]
        stdout: StdioCollector { id: ramOut }
        onExited: ramText.text = "🧠 " + ramOut.text.trim() + "%"
    }

    Process {
        id: cpuProc
        command: ["bash", "-c", "top -bn1 | grep \"Cpu(s)\" | sed \"s/.*, *\\([0-9.]*\\)%* id.*/\\1/\" | awk '{printf \"%.0f\", 100 - $1}'"]
        stdout: StdioCollector { id: cpuOut }
        onExited: cpuText.text = "⚙️ " + cpuOut.text.trim() + "%"
    }

    Timer {
        interval: 3000; running: true; repeat: true; triggeredOnStart: true
        onTriggered: { ramProc.running = true; cpuProc.running = true }
    }
}
