import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io

Item {
    id: netRoot
    implicitWidth: netRow.implicitWidth
    implicitHeight: netRow.implicitHeight

    property string currentSSID: ""
    property string connectionStatus: "Escaneando..."
    property bool isConnected: currentSSID !== ""
    property bool popupVisible: false
    property var wifiNetworks: []
    property string connectingSSID: ""

    Process {
        id: currentProc
        command: ["bash", "-c", "nmcli -t -f active,ssid dev wifi | grep '^yes' | cut -d: -f2"]
        stdout: StdioCollector { id: currentOut }
        onExited: {
            let ssid = currentOut.text.trim();
            netRoot.currentSSID = ssid;
            netRoot.connectionStatus = ssid !== "" ? ("Conectado a " + ssid) : "Sin conexión";
        }
    }

    Process {
        id: scanProc
        command: ["bash", "-c", "nmcli -t -f SSID,SIGNAL,SECURITY,IN-USE dev wifi list 2>/dev/null | head -20"]
        stdout: StdioCollector { id: scanOut }
        onExited: {
            let lines = scanOut.text.trim().split("\n");
            let nets = [];
            for (let i = 0; i < lines.length; i++) {
                let parts = lines[i].split(":");
                if (parts.length >= 3 && parts[0] !== "") {
                    let exists = false;
                    for (let j = 0; j < nets.length; j++) {
                        if (nets[j].ssid === parts[0]) { exists = true; break; }
                    }
                    if (!exists) {
                        nets.push({
                            ssid: parts[0],
                            signal: parseInt(parts[1]) || 0,
                            security: parts[2] || "",
                            inUse: parts[3] === "*"
                        });
                    }
                }
            }
            nets.sort(function(a, b) { return b.signal - a.signal; });
            netRoot.wifiNetworks = nets;
        }
    }

    Process {
        id: connectProc
        command: ["bash", "-c", "echo placeholder"]
        stdout: StdioCollector {}
        onExited: {
            netRoot.connectingSSID = "";
            currentProc.running = true;
            scanProc.running = true;
        }
    }

    Timer {
        interval: 5000; running: true; repeat: true; triggeredOnStart: true
        onTriggered: currentProc.running = true
    }

    // ── Indicador en barra ──
    RowLayout {
        id: netRow; spacing: 6
        Rectangle {
            Layout.alignment: Qt.AlignVCenter
            height: 32; width: netLabel.implicitWidth + 40
            radius: 16
            color: netHover.containsMouse ? "#514c1b" : "#2b2810"
            border.color: "#514c1b"; border.width: 1
            Behavior on color { ColorAnimation { duration: 150 } }

            RowLayout {
                anchors.centerIn: parent; spacing: 6
                Text { text: netRoot.isConnected ? "📶" : "📡"; font.pixelSize: 14 }
                Text {
                    id: netLabel
                    text: netRoot.isConnected ? netRoot.currentSSID : "WiFi"
                    color: netRoot.isConnected ? "#c8e882" : "#f0c830"
                    font.pixelSize: 12; font.bold: true; elide: Text.ElideRight
                }
            }
        }
    }

    MouseArea {
        id: netHover; anchors.fill: netRow
        hoverEnabled: true; cursorShape: Qt.PointingHandCursor
        onClicked: {
            netRoot.popupVisible = !netRoot.popupVisible;
            if (netRoot.popupVisible) scanProc.running = true;
        }
    }

    // ── Popup ──
    PopupWindow {
        id: netPopup
        anchor.item: netRoot; anchor.edges: Edges.Bottom; anchor.gravity: Edges.Bottom
        anchor.adjustment: PopupAdjustment.Slide
        implicitWidth: 300; implicitHeight: 400
        visible: netRoot.popupVisible
        color: "transparent"

        Rectangle {
            anchors.fill: parent
            color: "#1d1b09"; radius: 24
            border.color: "#514c1b"; border.width: 1

            opacity: netRoot.popupVisible ? 1.0 : 0.0
            scale:   netRoot.popupVisible ? 1.0 : 0.95
            Behavior on opacity { NumberAnimation { duration: 200; easing.type: Easing.OutSine } }
            Behavior on scale   { NumberAnimation { duration: 250; easing.type: Easing.OutBack } }

            ColumnLayout {
                anchors.fill: parent; anchors.margins: 16; spacing: 8

                // Header
                RowLayout {
                    spacing: 8
                    Text { text: "📶 Redes WiFi"; color: "#fef3c7"; font.pixelSize: 15; font.bold: true }
                    Item { Layout.fillWidth: true }
                    // Rescan
                    Rectangle {
                        width: 28; height: 28; radius: 14
                        color: rescanArea.containsMouse ? "#514c1b" : "#2b2810"
                        Behavior on color { ColorAnimation { duration: 120 } }
                        scale: rescanArea.containsMouse ? 1.1 : 1.0
                        Behavior on scale { NumberAnimation { duration: 120; easing.type: Easing.OutBack } }
                        Text {
                            anchors.centerIn: parent; text: "🔄"; font.pixelSize: 13
                            RotationAnimation on rotation { id: spinAnim; from: 0; to: 360; duration: 800; running: false }
                        }
                        MouseArea {
                            id: rescanArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                            onClicked: { spinAnim.running = true; scanProc.running = true; }
                        }
                    }
                    // Cerrar
                    Rectangle {
                        width: 28; height: 28; radius: 14
                        color: closeArea.containsMouse ? "#cc6e28" : "#2b2810"
                        Behavior on color { ColorAnimation { duration: 120 } }
                        Text { anchors.centerIn: parent; text: "✕"; font.pixelSize: 11; color: "#fef3c7" }
                        MouseArea { id: closeArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: netRoot.popupVisible = false }
                    }
                }

                // Estado actual
                Rectangle {
                    Layout.fillWidth: true; height: 32; radius: 10; color: "#2b2810"
                    RowLayout {
                        anchors.fill: parent; anchors.margins: 8; spacing: 6
                        Text { text: netRoot.isConnected ? "✅" : "❌"; font.pixelSize: 12 }
                        Text {
                            text: netRoot.connectionStatus
                            color: netRoot.isConnected ? "#96c836" : "#cc6e28"
                            font.pixelSize: 11; font.bold: true; elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: "#393616" }

                // Lista de redes
                Flickable {
                    Layout.fillWidth: true; Layout.fillHeight: true
                    contentHeight: netListCol.implicitHeight; clip: true

                    Column {
                        id: netListCol; width: parent.width; spacing: 4

                        Repeater {
                            model: netRoot.wifiNetworks.length

                            Rectangle {
                                required property int index
                                property var net: netRoot.wifiNetworks[index]
                                property bool isCurrentNet: net.ssid === netRoot.currentSSID
                                property bool isConnecting: net.ssid === netRoot.connectingSSID

                                width: netListCol.width; height: 44; radius: 10
                                color: netItemArea.containsMouse ? "#393616" : (isCurrentNet ? "#2b281080" : "transparent")
                                Behavior on color { ColorAnimation { duration: 120 } }

                                RowLayout {
                                    anchors.fill: parent; anchors.margins: 8; spacing: 8

                                    Text {
                                        text: net.signal >= 50 ? "📶" : "📡"
                                        font.pixelSize: 14; Layout.alignment: Qt.AlignVCenter
                                    }

                                    Column {
                                        Layout.fillWidth: true; Layout.alignment: Qt.AlignVCenter; spacing: 1
                                        Text {
                                            text: net.ssid
                                            color: isCurrentNet ? "#96c836" : "#fef3c7"
                                            font.pixelSize: 12; font.bold: true
                                            elide: Text.ElideRight; width: parent.width
                                        }
                                        Text {
                                            text: {
                                                let p = [net.signal + "%"];
                                                if (net.security !== "" && net.security !== "--") p.push("🔒");
                                                if (isCurrentNet) p.push("Conectado");
                                                if (isConnecting) p.push("Conectando...");
                                                return p.join("  ");
                                            }
                                            color: "#9e8438"; font.pixelSize: 9
                                        }
                                    }

                                    // Barras de señal
                                    Row {
                                        spacing: 2; Layout.alignment: Qt.AlignVCenter
                                        Repeater {
                                            model: 4
                                            Rectangle {
                                                required property int index
                                                width: 3; height: 6 + index * 4; radius: 1
                                                color: net.signal >= (index + 1) * 25
                                                    ? (isCurrentNet ? "#96c836" : "#f0c830")
                                                    : "#514c1b"
                                                anchors.bottom: parent.bottom
                                            }
                                        }
                                    }
                                }

                                MouseArea {
                                    id: netItemArea; anchors.fill: parent
                                    hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                    onClicked: {
                                        if (!isCurrentNet && !isConnecting) {
                                            netRoot.connectingSSID = net.ssid;
                                            connectProc.command = ["bash", "-c",
                                                "nmcli device wifi connect " + JSON.stringify(net.ssid)];
                                            connectProc.running = true;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
