import React, { useEffect, useState } from 'react';
import { Alert, Button, FlatList, Image, Text, TextInput, View } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';
import api from '../api/client';

export default function VisitsScreen() {
  const [visits, setVisits] = useState([]);
  const [notes, setNotes] = useState({});

  const loadVisits = () => api.get('/visits/mine').then((res) => setVisits(res.data));

  useEffect(() => {
    loadVisits().catch(() => {});
  }, []);

  const action = async (visitId, type) => {
    try {
      const pos = await Location.getCurrentPositionAsync({});
      await api.post(`/visits/${visitId}/${type}`, {
        latitude: pos.coords.latitude,
        longitude: pos.coords.longitude,
        note: notes[visitId] || '',
      });
      await loadVisits();
    } catch {
      Alert.alert('خطأ', 'فشلت عملية الزيارة');
    }
  };

  const uploadProof = async (visitId) => {
    const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!perm.granted) return Alert.alert('تنبيه', 'يلزم إذن الوصول للصور');
    const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], quality: 0.7 });
    if (result.canceled) return;
    try {
      const form = new FormData();
      const asset = result.assets[0];
      form.append('file', { uri: asset.uri, name: 'proof.jpg', type: 'image/jpeg' });
      form.append('note', notes[visitId] || '');
      await api.post(`/visits/${visitId}/proof`, form, { headers: { 'Content-Type': 'multipart/form-data' } });
      await loadVisits();
    } catch {
      Alert.alert('خطأ', 'فشل رفع صورة الإثبات');
    }
  };

  return (
    <FlatList
      style={{ flex: 1, padding: 16 }}
      data={visits}
      keyExtractor={(item) => item.id}
      renderItem={({ item }) => (
        <View style={{ marginBottom: 12, backgroundColor: '#fff', padding: 12, borderRadius: 8 }}>
          <Text>{item.customer_name}</Text>
          <Text>الحالة: {item.status}</Text>
          <TextInput
            placeholder="ملاحظة السائق"
            value={notes[item.id] || ''}
            onChangeText={(t) => setNotes((s) => ({ ...s, [item.id]: t }))}
            style={{ borderWidth: 1, borderColor: '#ddd', padding: 8, marginVertical: 8 }}
          />
          <Button title="تسجيل الوصول" onPress={() => action(item.id, 'check-in')} />
          <Button title="تسجيل المغادرة" onPress={() => action(item.id, 'check-out')} />
          <Button title="رفع صورة إثبات" onPress={() => uploadProof(item.id)} />
          {item.proof_image_url ? <Image source={{ uri: `${process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000'}${item.proof_image_url}` }} style={{ height: 90, marginTop: 6 }} /> : null}
        </View>
      )}
    />
  );
}
