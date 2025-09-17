import React from 'react';
import { SafeAreaView, Platform } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import WebView from 'react-native-webview';

const SERVER_URL = 'http://127.0.0.1:8002/';

export default function App() {
  // For LAN testing, replace 127.0.0.1 with your machine IP, e.g., http://192.168.1.10:8002/
  const uri = SERVER_URL;

  return (
    <SafeAreaView style={{ flex: 1 }}>
      <StatusBar style={Platform.OS === 'ios' ? 'dark' : 'light'} />
      <WebView
        source={{ uri }}
        originWhitelist={["*"]}
        allowsInlineMediaPlayback
        javaScriptEnabled
        domStorageEnabled
        startInLoadingState
        mixedContentMode="always"
        allowsBackForwardNavigationGestures
        style={{ flex: 1 }}
      />
    </SafeAreaView>
  );
}


