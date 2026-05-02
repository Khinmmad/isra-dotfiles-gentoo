import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import Quickshell.Services.Mpris

Item {
    id: musicRoot
    implicitWidth: musicRow.implicitWidth
    implicitHeight: musicRow.implicitHeight

    // ── Tiempo real ──
    property double localPosition: 0
    property bool isDraggingProgress: false

    Timer {
        id: smoothTimer; interval: 500; repeat: true
        running: player?.playbackState === MprisPlaybackState.Playing && !isDraggingProgress
        onTriggered: {
            musicRoot.localPosition += 500000;
            if (player && musicRoot.localPosition > player.length)
                musicRoot.localPosition = player.length;
        }
    }

    Connections {
        target: player ?? null
        function onPositionChanged()   { if (!isDraggingProgress) musicRoot.localPosition = player.position; }
        function onTrackTitleChanged() { musicRoot.localPosition = 0; }
    }

    function formatTime(ms) {
        if (!ms || ms < 0) return "0:00";
        let s = Math.floor(ms / 1000000);
        return Math.floor(s / 60) + ":" + (s % 60 < 10 ? "0" : "") + (s % 60);
    }

    readonly property var spotifyPlayer: {
        let players = Mpris.players.values;
        let sp = players.find(p => p.dbusName.includes("spotify"));
        return sp ?? (players.length > 0 ? players[0] : null);
    }

    property var player: spotifyPlayer
    property bool isSpotify: player ? player.dbusName.includes("spotify") : false

    Process { id: spotifyLaunch; command: ["spotify"] }

    // Popup — controlado por click
    property bool popupVisible: false

    RowLayout {
        id: musicRow; spacing: 6
        Rectangle { width: 1; height: 24; color: "#514c1b"; Layout.alignment: Qt.AlignVCenter }
        Loader { id: contentLoader; Layout.alignment: Qt.AlignVCenter; sourceComponent: player ? playingComponent : idleComponent }
    }

    Component {
        id: playingComponent
        RowLayout {
            spacing: 6
            Text { text: musicRoot.isSpotify ? "🎵" : "♫"; color: musicRoot.isSpotify ? "#1dd35f" : "#c8e882"; font.pixelSize: 15 }
            Text { text: player?.trackTitle ?? ""; color: "#fef3c7"; font.pixelSize: 12; font.bold: true; elide: Text.ElideRight; Layout.maximumWidth: 120 }
            Row {
                spacing: 2
                MusicIconBtn { text: "⏮"; onClicked: player?.previous() }
                MusicIconBtn {
                    text: player?.playbackState === MprisPlaybackState.Playing ? "⏸" : "▶"
                    iconColor: musicRoot.isSpotify ? "#1db954" : "#fef3c7"
                    onClicked: player?.togglePlaying()
                }
                MusicIconBtn { text: "⏭"; onClicked: player?.next() }
            }
        }
    }

    Component {
        id: idleComponent
        RowLayout {
            spacing: 8
            Rectangle {
                width: 130; height: 26; radius: 13
                color: launchArea.containsMouse ? "#2b2810" : "transparent"
                border.color: launchArea.containsMouse ? "#514c1b" : "transparent"
                Text { anchors.centerIn: parent; text: "🎵 Iniciar Spotify"; color: launchArea.containsMouse ? "#1dd35f" : "#f0c830"; font.pixelSize: 11; font.bold: true }
                MouseArea { id: launchArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: spotifyLaunch.running = true }
            }
        }
    }

    MouseArea {
        id: musicHover; anchors.fill: musicRow
        hoverEnabled: true; cursorShape: Qt.PointingHandCursor
        propagateComposedEvents: true
        onClicked: (mouse) => {
            mouse.accepted = false;
            if (player) musicRoot.popupVisible = !musicRoot.popupVisible;
        }
    }

    component MusicIconBtn: Rectangle {
        property string text: ""
        property string iconColor: "#fef3c7"
        signal clicked()
        width: 20; height: 20; radius: 10
        color: mArea.containsMouse ? "#514c1b" : "transparent"
        Text { anchors.centerIn: parent; text: parent.text; color: parent.iconColor; font.pixelSize: 10 }
        MouseArea { id: mArea; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: parent.clicked() }
    }

    PopupWindow {
        id: musicPopup
        anchor.item: musicRoot; anchor.edges: Edges.Bottom; anchor.gravity: Edges.Bottom
        anchor.adjustment: PopupAdjustment.Slide
        implicitWidth: 320; implicitHeight: 340
        visible: musicRoot.popupVisible && player !== null
        color: "transparent"

        Rectangle {
            id: popupBg; anchors.fill: parent
            color: "#1d1b09"; radius: 24
            border.color: "#514c1b"; border.width: 1

            opacity: musicRoot.popupVisible ? 1.0 : 0.0
            scale:   musicRoot.popupVisible ? 1.0 : 0.95
            Behavior on opacity { NumberAnimation { duration: 200 } }
            Behavior on scale   { NumberAnimation { duration: 250; easing.type: Easing.OutBack } }

            ColumnLayout {
                anchors.fill: parent; anchors.margins: 20; spacing: 12

                RowLayout {
                    spacing: 8
                    Text {
                        text: musicRoot.isSpotify ? "🎵 Spotify" : ("♫ " + (player?.identity ?? "Media"))
                        color: musicRoot.isSpotify ? "#1db954" : "#96c836"
                        font.pixelSize: 14; font.bold: true
                    }
                    Item { Layout.fillWidth: true }
                    Text {
                        text: player?.playbackState === MprisPlaybackState.Playing ? "Reproduciendo" : "Pausado"
                        color: "#9e8438"; font.pixelSize: 10; font.bold: true
                    }
                    Rectangle {
                        width: 22; height: 22; radius: 11
                        color: closeBtn.containsMouse ? "#cc6e28" : "#2b2810"
                        Behavior on color { ColorAnimation { duration: 120 } }
                        Text { anchors.centerIn: parent; text: "✕"; font.pixelSize: 10; color: "#fef3c7" }
                        MouseArea { id: closeBtn; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: musicRoot.popupVisible = false }
                    }
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: "#393616" }

                Column {
                    Layout.fillWidth: true; spacing: 4
                    Text { text: player?.trackTitle ?? "Sin título"; color: "#fef3c7"; font.pixelSize: 18; font.bold: true; elide: Text.ElideRight; width: parent.width }
                    Text {
                        text: {
                            if (!player) return "";
                            let a = player.trackArtists;
                            if (!a) return "";
                            if (typeof a === "object" && a.length !== undefined) return Array.from(a).join(", ");
                            return String(a);
                        }
                        color: "#ddc880"; font.pixelSize: 14; elide: Text.ElideRight; width: parent.width
                    }
                    Text { text: player?.trackAlbum ?? ""; color: "#9e8438"; font.pixelSize: 11; font.italic: true; visible: text !== ""; elide: Text.ElideRight; width: parent.width }
                }

                // Progreso
                ColumnLayout {
                    Layout.fillWidth: true; spacing: 4
                    Rectangle {
                        id: progressBar; Layout.fillWidth: true; height: 6; radius: 3; color: "#393616"
                        Rectangle {
                            height: parent.height; radius: 3
                            width: parent.width * (Math.min(musicRoot.localPosition, player?.length || 1) / (player?.length || 1))
                            color: musicRoot.isSpotify ? "#1db954" : "#f0c830"
                        }
                        MouseArea {
                            anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                            function updatePos(mx) {
                                if (player && player.length > 0)
                                    musicRoot.localPosition = Math.max(0, Math.min(1, mx / width)) * player.length;
                            }
                            onPressed: (m) => { musicRoot.isDraggingProgress = true; updatePos(m.x) }
                            onPositionChanged: (m) => { if (pressed) updatePos(m.x) }
                            onReleased: { if (player) player.position = musicRoot.localPosition; musicRoot.isDraggingProgress = false; }
                        }
                    }
                    RowLayout {
                        Text { text: formatTime(musicRoot.localPosition); color: "#9e8438"; font.pixelSize: 10 }
                        Item { Layout.fillWidth: true }
                        Text { text: formatTime(player?.length); color: "#9e8438"; font.pixelSize: 10 }
                    }
                }

                // Volumen
                RowLayout {
                    spacing: 10; Layout.fillWidth: true
                    Text { text: "󰕾"; color: "#9e8438"; font.pixelSize: 14 }
                    Rectangle {
                        id: volBar; Layout.fillWidth: true; height: 4; radius: 2; color: "#393616"
                        Rectangle {
                            height: parent.height; radius: 2
                            width: parent.width * (player?.volume || 0)
                            color: "#ddc880"
                        }
                        MouseArea {
                            anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                            function updateVol(mx) {
                                if (player) player.volume = Math.max(0, Math.min(1, mx / width));
                            }
                            onPressed: (m) => updateVol(m.x)
                            onPositionChanged: (m) => { if (pressed) updateVol(m.x) }
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter; spacing: 20
                    ControlBtn { text: "⏮"; size: 40; onClicked: player?.previous() }
                    ControlBtn { text: player?.playbackState === MprisPlaybackState.Playing ? "⏸" : "▶"; size: 50; accent: true; onClicked: player?.togglePlaying() }
                    ControlBtn { text: "⏭"; size: 40; onClicked: player?.next() }
                }
            }
        }
    }

    component ControlBtn: Rectangle {
        property string text: ""
        property int size: 40
        property bool accent: false
        signal clicked()
        width: size; height: size; radius: size / 2
        color: btnM.containsMouse
            ? (accent ? (musicRoot.isSpotify ? "#1db954" : "#f0c830") : "#514c1b")
            : "#2b2810"
        scale: btnM.pressed ? 0.9 : (btnM.containsMouse ? 1.1 : 1.0)
        Behavior on scale { NumberAnimation { duration: 100 } }
        Text {
            anchors.centerIn: parent; text: parent.text
            font.pixelSize: parent.size * 0.45
            color: parent.accent && btnM.containsMouse ? "#1d1b09" : "#fef3c7"
        }
        MouseArea { id: btnM; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: parent.clicked() }
    }
}
