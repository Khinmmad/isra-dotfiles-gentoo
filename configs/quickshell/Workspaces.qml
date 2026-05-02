import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Hyprland

ColumnLayout {
    spacing: 8

    Repeater {
        model: 10

        Item {
            id: wsItem
            required property int index
            property int wsId: index + 1

            readonly property var wsObject: {
                let all = Hyprland.workspaces.values;
                if (!all) return null;
                for (let i = 0; i < all.length; i++) {
                    if (all[i].id === wsId) return all[i];
                }
                return null;
            }

            readonly property bool isFocused: {
                if (!Hyprland.focusedMonitor) return false;
                if (!Hyprland.focusedMonitor.activeWorkspace) return false;
                return Hyprland.focusedMonitor.activeWorkspace.id === wsId;
            }

            readonly property bool hasWindows: wsObject !== null

            Layout.alignment: Qt.AlignHCenter
            width: 26
            height: 26

            // ── Bolita amarilla (workspaces no activos) ──
            Rectangle {
                anchors.centerIn: parent
                width: wsItem.isFocused ? 0 : (wsItem.hasWindows ? 13 : 9)
                height: width
                radius: width / 2
                color: "#FFD700"
                opacity: wsItem.hasWindows ? 0.95 : 0.45

                Behavior on width   { NumberAnimation { duration: 250; easing.type: Easing.OutBack } }
                Behavior on opacity { NumberAnimation { duration: 200 } }
            }

            // ── Pacman (workspace activo) ──
            Canvas {
                id: pacman
                anchors.centerIn: parent
                width: wsItem.isFocused ? 24 : 0
                height: width

                Behavior on width { NumberAnimation { duration: 300; easing.type: Easing.OutBack } }

                property real mouthAngle: 5

                SequentialAnimation on mouthAngle {
                    running: wsItem.isFocused
                    loops: Animation.Infinite
                    NumberAnimation { to: 32; duration: 280; easing.type: Easing.InOutSine }
                    NumberAnimation { to: 5;  duration: 280; easing.type: Easing.InOutSine }
                }

                onMouthAngleChanged: requestPaint()
                onWidthChanged:      requestPaint()

                onPaint: {
                    var ctx = getContext("2d");
                    ctx.clearRect(0, 0, width, height);
                    if (width <= 1) return;

                    var cx = width  / 2;
                    var cy = height / 2;
                    var r  = Math.min(width, height) / 2 - 1;
                    var mRad = mouthAngle * Math.PI / 180;

                    // Cuerpo amarillo
                    ctx.fillStyle = "#FFD700";
                    ctx.beginPath();
                    ctx.moveTo(cx, cy);
                    ctx.arc(cx, cy, r, mRad, 2 * Math.PI - mRad);
                    ctx.closePath();
                    ctx.fill();

                    // Ojo
                    ctx.fillStyle = "#1a1a2e";
                    ctx.beginPath();
                    ctx.arc(cx + r * 0.18, cy - r * 0.45, r * 0.13, 0, 2 * Math.PI);
                    ctx.fill();
                }
            }

            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: Hyprland.dispatch("workspace " + wsId)
            }
        }
    }
}
