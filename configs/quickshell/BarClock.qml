import QtQuick
import QtQuick.Layouts
import Quickshell

Item {
    id: clockRoot
    implicitWidth: 120
    implicitHeight: 32

    property date currentTime: new Date()

    property bool barHovered: clockHover.containsMouse
    property bool popupHovered: false
    property bool anyHovered: barHovered || popupHovered
    property bool popupVisible: false

    onAnyHoveredChanged: {
        if (anyHovered) { hideTimer.stop(); showTimer.start() }
        else            { showTimer.stop(); hideTimer.start() }
    }

    Timer { id: showTimer; interval: 200; onTriggered: clockRoot.popupVisible = true }
    Timer { id: hideTimer; interval: 500; onTriggered: if (!clockRoot.anyHovered) clockRoot.popupVisible = false }

    Timer {
        interval: 1000; running: true; repeat: true
        onTriggered: currentTime = new Date()
    }

    Rectangle {
        anchors.fill: parent
        radius: 16
        color: "#2b2810"
        border.color: "#514c1b"
        border.width: 1

        Column {
            anchors.centerIn: parent
            spacing: 0

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Qt.formatTime(currentTime, "h:mm ap")
                color: "#fef3c7"
                font.pixelSize: 13; font.bold: true
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: Qt.formatDate(currentTime, "ddd d 'de' MMM")
                color: "#f0c830"
                font.pixelSize: 9
            }
        }

        MouseArea { id: clockHover; anchors.fill: parent; hoverEnabled: true }
    }

    PopupWindow {
        id: datePopup
        anchor.item: clockRoot
        anchor.edges: Edges.Bottom
        anchor.gravity: Edges.Bottom
        anchor.adjustment: PopupAdjustment.Slide
        implicitWidth: 220; implicitHeight: 90
        visible: clockRoot.popupVisible
        color: "transparent"

        Rectangle {
            width: 220; height: 90
            color: "#1d1b09"; radius: 20
            border.color: "#514c1b"; border.width: 1

            opacity: clockRoot.popupVisible ? 1.0 : 0.0
            scale:   clockRoot.popupVisible ? 1.0 : 0.95
            Behavior on opacity { NumberAnimation { duration: 200 } }
            Behavior on scale   { NumberAnimation { duration: 250; easing.type: Easing.OutBack } }

            MouseArea {
                anchors.fill: parent; hoverEnabled: true
                onContainsMouseChanged: clockRoot.popupHovered = containsMouse
            }

            ColumnLayout {
                anchors.fill: parent; anchors.margins: 16; spacing: 8

                Text {
                    text: "Calendario y Fecha"
                    color: "#f0c830"
                    font.pixelSize: 12; font.bold: true
                    Layout.alignment: Qt.AlignHCenter
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: "#393616" }

                Text {
                    text: Qt.formatDate(currentTime, "dddd")
                    color: "#fef3c7"
                    font.pixelSize: 16; font.bold: true
                    Layout.alignment: Qt.AlignHCenter
                }
                Text {
                    text: Qt.formatDate(currentTime, "d 'de' MMMM, yyyy")
                    color: "#ddc880"
                    font.pixelSize: 13
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
    }
}
