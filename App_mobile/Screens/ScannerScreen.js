import React, { useState, useRef, useEffect } from 'react';
import { 
  View, Text, TouchableOpacity, StyleSheet, Image, 
  ActivityIndicator, Alert, Dimensions, SafeAreaView, Platform 
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera'; 
import * as ImagePicker from 'expo-image-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';
import { API_URL } from '../config';

const { width } = Dimensions.get('window');

const PLANTNET_API_KEY = "2b10FSp4CL2Gxo9D4GjQHbUu";
const PLANTNET_URL = "https://my-api.plantnet.org/v2/identify/all";

export default function ScannerScreen({ navigation, route }) {
  const [permission, requestPermission] = useCameraPermissions();
  const [photo, setPhoto] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const cameraRef = useRef(null);

  useEffect(() => {
    (async () => {
      if (!permission || !permission.granted) {
        await requestPermission();
      }
    })();
  }, [permission]);

  useEffect(() => {
    if (route.params?.openGallery) {
      pickImage();
    }
  }, [route.params]);

  const takePicture = async () => {
    if (cameraRef.current) {
      try {
        const photoData = await cameraRef.current.takePictureAsync({ quality: 0.7 });
        setPhoto(photoData);
        analyzePlant(photoData.uri);
      } catch (e) {
        Alert.alert("Erreur", "Impossible de capturer l'image");
      }
    }
  };

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({ 
      mediaTypes: ImagePicker.MediaTypeOptions.Images, 
      quality: 0.7 
    });
    if (!result.canceled) {
      setPhoto({ uri: result.assets[0].uri });
      analyzePlant(result.assets[0].uri);
    }
  };

  // 🔥 Sauvegarde sur le serveur Python (MySQL)
  const saveScanToServer = async (scanResult) => {
    try {
      const userId = await AsyncStorage.getItem('userId');
      if (!userId) return;
      
      const response = await fetch(`${API_URL}/save-scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: parseInt(userId),
          nom_plante: scanResult.nom_fr,
          nom_scientifique: scanResult.nom_sci || '',
          famille: scanResult.famille || '',
          score: scanResult.score / 100,
          details: JSON.stringify(scanResult.details),
          image_url: scanResult.image_uri || ''
        })
      });
      
      const data = await response.json();
      console.log('📡 Réponse serveur Python:', data);
    } catch (error) {
      console.error('❌ Erreur de connexion:', error);
    }
  };

  const analyzePlant = async (imageUri) => {
    setAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append('images', { uri: imageUri, name: 'plant.jpg', type: 'image/jpeg' });
      
      const plantNetResponse = await fetch(`${PLANTNET_URL}?api-key=${PLANTNET_API_KEY}&lang=fr`, { 
        method: 'POST', body: formData 
      });
      
      const plantData = await plantNetResponse.json();
      if (!plantData.results || plantData.results.length === 0) throw new Error("Plante non reconnue");

      const meilleur = plantData.results[0];
      const nomFr = meilleur.species.commonNames?.[0] || meilleur.species.scientificNameWithoutAuthor;
      const nomScientifique = meilleur.species.scientificName || '';
      const famille = meilleur.species.family?.scientificName || '';
      const score = Math.round(meilleur.score * 100);

      // 🔥 Appel au backend Python pour l'analyse détaillée
      const response = await fetch(`${API_URL}/analyze-plant`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nom_plante: nomFr })
      });
      const data = await response.json();
      if (data.status !== 'success') throw new Error(data.message || "Analyse échouée");
      const details = data.analyse;  // déjà un objet JSON

      const scanResult = { 
        nom_fr: nomFr,
        nom_sci: nomScientifique,
        famille: famille,
        score: score,
        details: details,
        image_uri: imageUri,
        date: new Date().toISOString()
      };

      await saveScanToServer(scanResult);
      navigation.replace('Main', { lastScan: scanResult });

    } catch (e) {
      console.error(e);
      Alert.alert("Oups", "Identification impossible.");
      setPhoto(null);
    } finally {
      setAnalyzing(false);
    }
  };

  // --- UI inchangée ---
  if (!permission) return <View style={styles.container} />;
  if (!permission.granted) return (
    <View style={styles.container}>
      <Text style={{color: '#fff', textAlign: 'center', marginTop: 100}}>
        Veuillez autoriser l'accès à la caméra.
      </Text>
    </View>
  );

  return (
    <View style={styles.container}>
      {!photo ? (
        <View style={styles.cameraWrapper}>
          <CameraView ref={cameraRef} style={StyleSheet.absoluteFill} facing="back" />
          <SafeAreaView style={styles.uiOverlay}>
            <View style={styles.topBar}>
              <TouchableOpacity onPress={() => navigation.goBack()} style={styles.closeButton}>
                <Ionicons name="close" size={38} color="#fff" />
              </TouchableOpacity>
              <Text style={styles.title}>SCANNER</Text>
              <TouchableOpacity onPress={pickImage} style={styles.galleryButton}>
                <Ionicons name="images" size={30} color="#fff" />
              </TouchableOpacity>
            </View>
            <View style={styles.scannerFrame} />
            <View style={styles.bottomBar}>
              <TouchableOpacity style={styles.shutter} onPress={takePicture}>
                <View style={styles.shutterInternal} />
              </TouchableOpacity>
            </View>
          </SafeAreaView>
        </View>
      ) : (
        <View style={styles.preview}>
          <Image source={{ uri: photo.uri }} style={styles.fullImage} />
          {analyzing && (
            <View style={styles.loaderContainer}>
              <ActivityIndicator size="large" color="#32C59A" />
              <Text style={styles.loaderText}>ANALYSE EN COURS...</Text>
            </View>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  cameraWrapper: { flex: 1 },
  uiOverlay: { ...StyleSheet.absoluteFillObject, justifyContent: 'space-between', alignItems: 'center', zIndex: 10 },
  topBar: { flexDirection: 'row', width: '100%', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, marginTop: Platform.OS === 'android' ? 35 : 10 },
  title: { color: '#fff', fontWeight: 'bold', letterSpacing: 3, fontSize: 14 },
  closeButton: { padding: 10 },
  galleryButton: { padding: 10 },
  scannerFrame: { width: width * 0.7, height: width * 0.7, borderWidth: 2, borderColor: 'rgba(255,255,255,0.4)', borderRadius: 30 },
  bottomBar: { marginBottom: 40 },
  shutter: { width: 84, height: 84, borderRadius: 42, backgroundColor: 'rgba(255,255,255,0.2)', justifyContent: 'center', alignItems: 'center', borderWidth: 4, borderColor: '#fff' },
  shutterInternal: { width: 66, height: 66, borderRadius: 33, backgroundColor: '#fff' },
  preview: { flex: 1 },
  fullImage: { width: '100%', height: '100%' },
  loaderContainer: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.7)', justifyContent: 'center', alignItems: 'center' },
  loaderText: { color: '#fff', marginTop: 20, fontWeight: '800', letterSpacing: 2 }
});