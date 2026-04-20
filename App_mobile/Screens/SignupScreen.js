import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, ImageBackground, StyleSheet, Alert } from 'react-native';
import { API_URL } from '../config'; // Utilisation de l'URL unifiée

export default function SignupScreen({ navigation }) {
  const [nom, setNom] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const SendSignup = async () => {
    // Vérification que les champs ne sont pas vides
    if (!nom || !email || !password) {
      Alert.alert("Champs manquants", "Merci de remplir toutes les informations.");
      return;
    }

    try {
      // Appel au serveur Python (FastAPI)
      const response = await fetch(`${API_URL}/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nom, email, password })
      });

      const data = await response.json();

      if (data.status === 'success') {
        Alert.alert('Succès', 'Compte créé avec succès ! 🌿');
        navigation.navigate('Login');
      } else {
        // Affiche l'erreur venant du Python (ex: "Cet email existe déjà")
        Alert.alert('Erreur', data.message);
      }
    } catch (error) {
      console.error(error);
      Alert.alert('Erreur', 'Connexion impossible au serveur Python (Signup).');
    }
  };

  return (
    <ImageBackground
      source={require('../../assets/background.png')}
      style={styles.background}
    >
      <View style={styles.overlay}>
        <View style={styles.card}>
          <Text style={styles.titre}>Créer un compte</Text>
          <Text style={styles.sousTitre}>Rejoins WhatAPlant 🌿</Text>

          <TextInput
            style={styles.input}
            placeholder="Nom complet"
            placeholderTextColor="rgba(255,255,255,0.6)"
            value={nom}
            onChangeText={setNom}
          />

          <TextInput
            style={styles.input}
            placeholder="Email"
            placeholderTextColor="rgba(255,255,255,0.6)"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none" // Évite la majuscule automatique sur l'email
          />

          <TextInput
            style={styles.input}
            placeholder="Mot de passe"
            placeholderTextColor="rgba(255,255,255,0.6)"
            value={password}
            onChangeText={setPassword}
            secureTextEntry={true}
          />

          <TouchableOpacity style={styles.bouton} onPress={SendSignup}>
            <Text style={styles.boutonTexte}>S'inscrire</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.lien}
            onPress={() => navigation.navigate('Login')}
          >
            <Text style={styles.lienTexte}>Déjà un compte ? Se connecter</Text>
          </TouchableOpacity>
        </View>
      </View>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  background: { flex: 1 },
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    padding: 24,
  },
  card: { alignItems: 'center' },
  titre: { fontSize: 32, fontWeight: 'bold', color: '#fff', marginBottom: 8 },
  sousTitre: { fontSize: 14, color: 'rgba(255,255,255,0.7)', marginBottom: 32 },
  input: {
    width: '100%',
    backgroundColor: 'rgba(255,255,255,0.15)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.4)',
    borderRadius: 12,
    padding: 14,
    color: '#fff',
    fontSize: 15,
    marginBottom: 16,
  },
  bouton: {
    width: '100%',
    backgroundColor: '#1D9E75',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
    marginBottom: 16,
  },
  boutonTexte: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  lien: { marginTop: 8 },
  lienTexte: { color: 'rgba(255,255,255,0.7)', fontSize: 13 },
});