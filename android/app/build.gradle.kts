plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}
android {
    namespace = "com.ruslansharifov.pccontroller"
    compileSdk = 35
    defaultConfig {
        applicationId = "com.ruslansharifov.pccontroller"
        minSdk = 26
        targetSdk = 35
        versionCode = 2
        versionName = "2.0.0"
    }
}
