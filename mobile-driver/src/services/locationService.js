import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';
import api from '../api/client';

export const DRIVER_LOCATION_TASK = 'driver-location-task';

TaskManager.defineTask(DRIVER_LOCATION_TASK, async ({ data, error }) => {
  if (error || !data?.locations?.length) return;
  const points = data.locations.map((loc) => ({
    latitude: loc.coords.latitude,
    longitude: loc.coords.longitude,
    speed_kmh: loc.coords.speed ? loc.coords.speed * 3.6 : null,
    captured_at: new Date(loc.timestamp).toISOString(),
  }));
  try {
    await api.post('/shifts/active/locations', { points });
  } catch {
    // retry policy can be added with local queue
  }
});

export async function startBackgroundTracking() {
  const { status } = await Location.requestForegroundPermissionsAsync();
  if (status !== 'granted') return false;
  await Location.requestBackgroundPermissionsAsync();
  await Location.startLocationUpdatesAsync(DRIVER_LOCATION_TASK, {
    accuracy: Location.Accuracy.Balanced,
    timeInterval: 30000,
    distanceInterval: 30,
    pausesUpdatesAutomatically: false,
  });
  return true;
}

export async function stopBackgroundTracking() {
  const started = await Location.hasStartedLocationUpdatesAsync(DRIVER_LOCATION_TASK);
  if (started) await Location.stopLocationUpdatesAsync(DRIVER_LOCATION_TASK);
}
