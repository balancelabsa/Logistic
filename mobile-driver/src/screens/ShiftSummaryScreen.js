import React, { useEffect, useState } from 'react';
import { Text, View } from 'react-native';
import api from '../api/client';

export default function ShiftSummaryScreen() {
  const [summary, setSummary] = useState({});
  useEffect(() => {
    api.get('/shifts/my-summary').then((res) => setSummary(res.data)).catch(() => {});
  }, []);

  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', gap: 8 }}>
      <Text>ملخص اليوم</Text>
      <Text>عدد الورديات: {summary.today_shifts || 0}</Text>
      <Text>إجمالي الدقائق: {summary.total_minutes || 0}</Text>
    </View>
  );
}
