package com.ruslansharifov.pccontroller

import android.annotation.SuppressLint
import android.app.Activity
import android.app.AlertDialog
import android.content.Context
import android.graphics.Color
import android.os.Bundle
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import android.view.ViewGroup
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import org.json.JSONObject
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.HttpURLConnection
import java.net.InetSocketAddress
import java.net.URL
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.spec.GCMParameterSpec
import kotlin.concurrent.thread

class MainActivity : Activity() {
    private lateinit var root: LinearLayout
    private lateinit var devicesPanel: LinearLayout
    private lateinit var status: TextView
    private val discovered = linkedMapOf<String, String>()
    @Volatile private var discoverySocket: DatagramSocket? = null
    private var activeWebView: WebView? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.rgb(11, 18, 32)
        window.navigationBarColor = Color.rgb(11, 18, 32)
        buildDiscoveryUi()
        startDiscovery()
        reconnectSaved()
    }

    private fun buildDiscoveryUi() {
        root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(24, 36, 24, 24)
            setBackgroundColor(Color.rgb(11, 18, 32))
        }
        val title = TextView(this).apply {
            text = "PC Controller"; textSize = 26f; setTextColor(Color.WHITE)
        }
        status = TextView(this).apply {
            text = "Searching for PCs on this Wi-Fi…"; textSize = 14f
            setTextColor(Color.LTGRAY); setPadding(0, 8, 0, 18)
        }
        val scan = Button(this).apply { text = "Scan local network"; setOnClickListener { startDiscovery() } }
        val manual = EditText(this).apply {
            hint = "PC address, e.g. 192.168.1.10:9050"; setSingleLine(true)
            setTextColor(Color.WHITE); setHintTextColor(Color.GRAY)
        }
        val manualConnect = Button(this).apply {
            text = "Connect using address"
            setOnClickListener {
                val raw = manual.text.toString().trim().removePrefix("http://").removePrefix("https://")
                val host = raw.substringBefore(":").substringBefore("/")
                val port = raw.substringAfter(":", "9050").substringBefore("/").toIntOrNull() ?: 9050
                if (host.isNotBlank()) askPairingCode(host, port)
            }
        }
        devicesPanel = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        root.addView(title); root.addView(status); root.addView(scan); root.addView(manual); root.addView(manualConnect)
        root.addView(TextView(this).apply {
            text = "Available computers"; textSize = 18f; setTextColor(Color.WHITE); setPadding(0, 22, 0, 8)
        })
        root.addView(devicesPanel)
        setContentView(root)
    }

    private fun startDiscovery() {
        discoverySocket?.close()
        thread(name = "pc-controller-discovery") {
            try {
                val socket = DatagramSocket(null).apply {
                    reuseAddress = true; broadcast = true; soTimeout = 1200
                    bind(InetSocketAddress(9051))
                }
                discoverySocket = socket
                val buffer = ByteArray(2048)
                while (!socket.isClosed) {
                    try {
                        val packet = DatagramPacket(buffer, buffer.size)
                        socket.receive(packet)
                        val json = JSONObject(String(packet.data, 0, packet.length, Charsets.UTF_8))
                        if (json.optString("service") != "pc-controller") continue
                        val host = packet.address.hostAddress ?: continue
                        val port = json.optInt("port", 9050)
                        val name = json.optString("device_name", "Windows PC")
                        synchronized(discovered) { discovered["$host:$port"] = name }
                        runOnUiThread { renderDiscovered() }
                    } catch (_: java.net.SocketTimeoutException) {
                    } catch (_: Exception) {
                    }
                }
            } catch (_: Exception) {
                runOnUiThread { status.text = "Discovery unavailable. Enter the PC address manually." }
            }
        }
    }

    private fun renderDiscovered() {
        devicesPanel.removeAllViews()
        val snapshot = synchronized(discovered) { discovered.toMap() }
        status.text = if (snapshot.isEmpty()) "Searching… Keep both devices on the same private Wi-Fi." else "${snapshot.size} computer(s) found"
        snapshot.forEach { (address, name) ->
            devicesPanel.addView(Button(this).apply {
                text = "$name  ·  $address"
                setOnClickListener {
                    askPairingCode(address.substringBefore(":"), address.substringAfter(":").toIntOrNull() ?: 9050)
                }
            })
        }
    }

    private fun askPairingCode(host: String, port: Int) {
        val input = EditText(this).apply {
            hint = "6-digit code shown on the PC"; setSingleLine(true)
            inputType = android.text.InputType.TYPE_CLASS_NUMBER
        }
        AlertDialog.Builder(this).setTitle("Pair with $host")
            .setMessage("Open the PC Controller tray menu and choose Pair a device.")
            .setView(input).setNegativeButton("Cancel", null)
            .setPositiveButton("Pair") { _, _ -> pair(host, port, input.text.toString()) }.show()
    }

    private fun pair(host: String, port: Int, code: String) {
        status.text = "Pairing…"
        thread(name = "pc-controller-pair") {
            try {
                val connection = (URL("http://$host:$port/api/pair").openConnection() as HttpURLConnection).apply {
                    requestMethod = "POST"; connectTimeout = 5000; readTimeout = 5000; doOutput = true
                    setRequestProperty("Content-Type", "application/json")
                }
                val body = JSONObject().put("code", code).put("device_name", android.os.Build.MODEL).toString()
                connection.outputStream.use { it.write(body.toByteArray(Charsets.UTF_8)) }
                val responseCode = connection.responseCode
                val stream = if (responseCode in 200..299) connection.inputStream else connection.errorStream
                val response = stream.bufferedReader().use { it.readText() }
                if (responseCode !in 200..299) throw IllegalStateException(JSONObject(response).optString("detail", "Pairing failed"))
                val token = JSONObject(response).getString("token")
                saveConnection(host, port, token)
                connection.disconnect()
                runOnUiThread { openRemote(host, port, token) }
            } catch (error: Exception) {
                runOnUiThread { status.text = error.message ?: "Could not pair with this PC" }
            }
        }
    }

    private fun saveConnection(host: String, port: Int, token: String) {
        getSharedPreferences("pc_controller", Context.MODE_PRIVATE).edit()
            .putString("host", host).putInt("port", port).putString("token", encryptToken(token)).apply()
    }

    private fun reconnectSaved() {
        val prefs = getSharedPreferences("pc_controller", Context.MODE_PRIVATE)
        val host = prefs.getString("host", null) ?: return
        val port = prefs.getInt("port", 9050)
        val encrypted = prefs.getString("token", null) ?: return
        try { openRemote(host, port, decryptToken(encrypted)) }
        catch (_: Exception) { status.text = "Saved pairing unavailable. Pair this device again." }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun openRemote(host: String, port: Int, token: String) {
        root.removeAllViews()
        val bar = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; setBackgroundColor(Color.rgb(17, 28, 46)) }
        bar.addView(TextView(this).apply {
            text = "Connected · $host"; setTextColor(Color.WHITE); textSize = 14f; setPadding(12, 14, 8, 14)
        }, LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f))
        bar.addView(Button(this).apply {
            text = "Disconnect"
            setOnClickListener {
                getSharedPreferences("pc_controller", Context.MODE_PRIVATE).edit().clear().apply()
                activeWebView?.destroy(); activeWebView = null; buildDiscoveryUi()
            }
        })
        val web = WebView(this).apply {
            settings.javaScriptEnabled = true; settings.domStorageEnabled = true
            webViewClient = object : WebViewClient() {
                private var injected = false
                override fun onPageFinished(view: WebView, url: String) {
                    if (!injected) {
                        injected = true
                        val encoded = JSONObject.quote(token)
                        view.evaluateJavascript("localStorage.setItem('pc_controller_token', $encoded); location.reload();", null)
                    }
                }
            }
        }
        activeWebView = web
        root.addView(bar)
        root.addView(web, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
        web.loadUrl("http://$host:$port/")
    }

    private fun getOrCreateKey(): java.security.Key {
        val alias = "pc_controller_token_key"
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        if (!store.containsAlias(alias)) {
            val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
            generator.init(KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build())
            generator.generateKey()
        }
        return store.getKey(alias, null) as java.security.Key
    }

    private fun encryptToken(token: String): String {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, getOrCreateKey())
        return Base64.encodeToString(cipher.iv + cipher.doFinal(token.toByteArray(Charsets.UTF_8)), Base64.NO_WRAP)
    }

    private fun decryptToken(value: String): String {
        val packed = Base64.decode(value, Base64.NO_WRAP)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, getOrCreateKey(), GCMParameterSpec(128, packed.copyOfRange(0, 12)))
        return String(cipher.doFinal(packed.copyOfRange(12, packed.size)), Charsets.UTF_8)
    }

    override fun onDestroy() {
        discoverySocket?.close(); activeWebView?.destroy(); super.onDestroy()
    }
}
