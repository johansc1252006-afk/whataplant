import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, ImageBackground, StyleSheet, Alert } from 'react-native';
import { API_URL } from '../config';
import { Ionicons } from '@expo/vector-icons';
import LottieView from 'lottie-react-native';

export default function SignupScreen({ navigation }) {
  const [nom, setNom] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isPasswordFocused, setIsPasswordFocused] = useState(false);
  const animationRef = useRef(null);
  const timeoutRef = useRef(null);

  // Nettoyage du timeout
  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  // Démarrer la boucle neutre (tout le Lottie) au montage
  useEffect(() => {
    if (animationRef.current) {
      animationRef.current.play(0, 392);
    }
  }, []);

  // Gérer le focus du mot de passe
  useEffect(() => {
    if (animationRef.current) {
      if (isPasswordFocused) {
        animationRef.current.play(186, 186); // yeux fermés
      } else {
        animationRef.current.play(0, 392);   // retour neutre
      }
    }
  }, [isPasswordFocused]);

  // Animation fâchée (erreur)
  const playAngry = () => {
    if (animationRef.current) {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      animationRef.current.play(313, 392);
      timeoutRef.current = setTimeout(() => {
        if (!isPasswordFocused) {
          animationRef.current?.play(0, 392);
        }
      }, 2000);
    }
  };

  const SendSignup = async () => {
    if (!nom || !email || !password) {
      Alert.alert("Champs manquants", "Merci de remplir toutes les informations.");
      playAngry();
      return;
    }

    try {
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
        Alert.alert('Erreur', data.message);
        playAngry();
      }
    } catch (error) {
      console.error(error);
      Alert.alert('Erreur', 'Connexion impossible au serveur Python (Signup).');
      playAngry();
    }
  };

  return (
    <ImageBackground source={require('../../assets/background.png')} style={styles.background}>
      <View style={styles.overlay}>
        <View style={styles.card}>
          <LottieView
            ref={animationRef}
            source={require('../../assets/animalot.json')}
            style={styles.avatar}
          />
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
            autoCapitalize="none"
          />

          <View style={styles.passwordContainer}>
            <TextInput
              style={[styles.input, styles.passwordInput]}
              placeholder="Mot de passe"
              placeholderTextColor="rgba(255,255,255,0.6)"
              value={password}
              onChangeText={setPassword}
              onFocus={() => setIsPasswordFocused(true)}
              onBlur={() => setIsPasswordFocused(false)}
              secureTextEntry={!showPassword}
            />
            <TouchableOpacity onPress={() => setShowPassword(!showPassword)} style={styles.eyeIcon}>
              <Ionicons name={showPassword ? "eye-off" : "eye"} size={24} color="rgba(255,255,255,0.6)" />
            </TouchableOpacity>
          </View>

          <TouchableOpacity style={styles.bouton} onPress={SendSignup}>
            <Text style={styles.boutonTexte}>S'inscrire</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.lien} onPress={() => navigation.navigate('Login')}>
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
  avatar: { width: 150, height: 150, marginBottom: 10 },
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
  passwordContainer: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    position: 'relative',
  },
  passwordInput: {
    marginBottom: 0,
  },
  eyeIcon: {
    position: 'absolute',
    right: 14,
    top: 12,
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