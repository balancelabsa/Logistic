import React, { useState } from 'react';
import { Alert, Button, StyleSheet, Text, TextInput, View } from 'react-native';
import { useAuth } from '../context/AuthContext';

export default function LoginScreen() {
  const { login } = useAuth();
  const [phone, setPhone] = useState('900000101');
  const [password, setPassword] = useState('Driver@1234');

  const onLogin = async () => {
    try {
      await login(phone, password);
    } catch {
      Alert.alert('خطأ', 'فشل تسجيل الدخول');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>تسجيل دخول السائق</Text>
      <TextInput style={styles.input} value={phone} onChangeText={setPhone} placeholder="رقم الجوال" />
      <TextInput style={styles.input} value={password} secureTextEntry onChangeText={setPassword} placeholder="كلمة المرور" />
      <Button title="دخول" onPress={onLogin} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 16, gap: 8 },
  title: { fontSize: 22, fontWeight: '700', marginBottom: 8, textAlign: 'center' },
  input: { borderWidth: 1, borderColor: '#ddd', borderRadius: 8, padding: 10 },
});
