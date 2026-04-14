import React, { useState } from 'react';
import { Alert, Button, Text, View } from 'react-native';
import api from '../api/client';
import { stopBackgroundTracking, startBackgroundTracking } from '../services/locationService';

export default function ShiftScreen({ navigation }) {
  const [shiftId, setShiftId] = useState(null);
  const [trackingState, setTrackingState] = useState('متوقف');

  const startShift = async () => {
    try {
      const { data } = await api.post('/shifts/start');
      setShiftId(data.shift_id);
      const started = await startBackgroundTracking();
      setTrackingState(started ? 'نشط بالخلفية' : 'فشل تشغيل التتبع');
    } catch {
      Alert.alert('خطأ', 'تعذر بدء الوردية');
    }
  };

  const endShift = async () => {
    if (!shiftId) return;
    try {
      await api.post(`/shifts/${shiftId}/end`);
      await stopBackgroundTracking();
      setShiftId(null);
      setTrackingState('متوقف');
    } catch {
      Alert.alert('خطأ', 'تعذر إنهاء الوردية');
    }
  };

  return (
    <View style={{ flex: 1, justifyContent: 'center', padding: 16, gap: 12 }}>
      <Text>حالة الوردية: {shiftId ? 'نشطة' : 'غير نشطة'}</Text>
      <Text>حالة التتبع: {trackingState}</Text>
      <Button title="بدء الوردية" onPress={startShift} />
      <Button title="إنهاء الوردية" onPress={endShift} />
      <Button title="الزيارات" onPress={() => navigation.navigate('Visits')} />
      <Button title="ملخص اليوم" onPress={() => navigation.navigate('Summary')} />
    </View>
  );
}
