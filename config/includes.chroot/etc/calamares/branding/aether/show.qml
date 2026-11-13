import QtQuick 2.0
import calamares.slideshow 1.0

Presentation {
    id: presentation
    titleColor: "#ffffff"
    textColor: "#e0ddff"
    fontFamily: "Noto Sans"
    loopSlides: true

    Slide {
        title: qsTr("AETHER OS is getting ready")
        centeredText: qsTr("A lightweight desktop, prepared for this computer.")
        content: [
            qsTr("System files are being copied to the selected disk."),
            qsTr("The progress indicator follows the installer jobs."),
            qsTr("Keep this computer powered on until installation finishes.")
        ]
    }

    Slide {
        title: qsTr("Your system, your settings")
        centeredText: qsTr("Choose the appearance and settings that fit your workflow.")
        content: [
            qsTr("XFCE provides the live desktop and system settings."),
            qsTr("The first-login setup saves your user preferences."),
            qsTr("AETHER does not include advertising or telemetry.")
        ]
    }

    Slide {
        title: qsTr("Installation is a real disk change")
        centeredText: qsTr("Review the disk and partition summary before confirming.")
        content: [
            qsTr("Calamares writes the system to the disk you selected."),
            qsTr("Remove the live medium after the installer asks you to restart."),
            qsTr("Optional compatibility components are not installed in this image.")
        ]
    }

    function onActivate() {
        presentation.currentSlide = 0
    }
}
