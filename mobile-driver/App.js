import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import LoginScreen from './src/screens/LoginScreen';
import ShiftScreen from './src/screens/ShiftScreen';
import VisitsScreen from './src/screens/VisitsScreen';
import ShiftSummaryScreen from './src/screens/ShiftSummaryScreen';
import { AuthProvider, useAuth } from './src/context/AuthContext';

const Stack = createNativeStackNavigator();

function Navigator() {
  const { token } = useAuth();
  return (
    <NavigationContainer>
      <Stack.Navigator>
        {!token ? (
          <Stack.Screen name="Login" component={LoginScreen} options={{ title: 'تسجيل الدخول' }} />
        ) : (
          <>
            <Stack.Screen name="Shift" component={ShiftScreen} options={{ title: 'حالة الوردية' }} />
            <Stack.Screen name="Visits" component={VisitsScreen} options={{ title: 'الزيارات الموكلة' }} />
            <Stack.Screen name="Summary" component={ShiftSummaryScreen} options={{ title: 'ملخص الوردية' }} />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Navigator />
    </AuthProvider>
  );
}
