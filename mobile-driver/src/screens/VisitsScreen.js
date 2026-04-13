import React, { useEffect, useState } from 'react';
import { Alert, Button, FlatList, Text, View } from 'react-native';
import * as Location from 'expo-location';
import api from '../api/client';

export default function VisitsScreen() {
  const [visits, setVisits] = useState([]);

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
        notes: `تم ${type}`,
      });
      await loadVisits();
    } catch {
      Alert.alert('خطأ', 'فشلت عملية الزيارة');
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
          <Text>{item.status}</Text>
          <Button title="Check-In" onPress={() => action(item.id, 'check-in')} />
          <Button title="Check-Out" onPress={() => action(item.id, 'check-out')} />
        </View>
      )}
    />
  );
}
