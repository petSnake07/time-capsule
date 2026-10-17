import React, { useEffect, useState } from 'react';
import { Alert, Pressable, SafeAreaView, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';

const API = process.env.EXPO_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';
type Group = { id: number; name: string; destination: string; member_count: number };
type Event = { id: number; title: string; event_date: string; location: string };

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, { headers: { 'Content-Type': 'application/json' }, ...options });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

export default function App() {
  const [tab, setTab] = useState('Scrapbook');
  const [groups, setGroups] = useState<Group[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [group, setGroup] = useState<Group | null>(null);
  const [steps, setSteps] = useState(0);
  const [contact, setContact] = useState('');
  const [handle, setHandle] = useState('@eddie');
  const [password, setPassword] = useState('');

  const load = async () => {
    try {
      const loaded = await api<Group[]>('/groups');
      setGroups(loaded); setGroup(loaded[0] || null);
      if (loaded[0]) setEvents(await api<Event[]>(`/calendar/${loaded[0].id}`));
    } catch (error) { Alert.alert('API unavailable', String(error)); }
  };
  useEffect(() => { load(); }, []);

  const createAccount = async () => {
    try {
      const result = await api<{ contact: string; demo_code: string }>('/auth/account', { method: 'POST', body: JSON.stringify({ contact, handle, password }) });
      Alert.alert('Account created', `Demo verification code: ${result.demo_code}`);
    } catch (error) { Alert.alert('Could not create account', String(error)); }
  };

  const renderContent = () => {
    if (tab === 'Groups') return <View><Text style={styles.heading}>Your trips</Text>{groups.map(item => <Pressable key={item.id} style={styles.card} onPress={() => { setGroup(item); setTab('Scrapbook'); }}><Text style={styles.cardTitle}>{item.name}</Text><Text style={styles.muted}>{item.destination} · {item.member_count} members</Text></Pressable>)}</View>;
    if (tab === 'Record') return <View style={styles.center}><Text style={styles.recordIcon}>●</Text><Text style={styles.heading}>Record a vlog</Text><Text style={styles.muted}>Camera and microphone permissions will be added in the Expo development build. Maximum length: 60 seconds.</Text><Pressable style={styles.primary}><Text style={styles.primaryText}>Start recording</Text></Pressable></View>;
    if (tab === 'Calendar') return <View><Text style={styles.heading}>Itinerary</Text>{events.map(event => <View key={event.id} style={styles.card}><Text style={styles.cardTitle}>{event.title}</Text><Text style={styles.muted}>{event.event_date} · {event.location}</Text></View>)}</View>;
    if (tab === 'Settings') return <View><Text style={styles.heading}>Account</Text><TextInput style={styles.input} placeholder="Email or phone" value={contact} onChangeText={setContact} autoCapitalize="none"/><TextInput style={styles.input} placeholder="@handle" value={handle} onChangeText={setHandle} autoCapitalize="none"/><TextInput style={styles.input} placeholder="Password (8+ chars, letters + numbers)" value={password} onChangeText={setPassword} secureTextEntry/><Pressable style={styles.primary} onPress={createAccount}><Text style={styles.primaryText}>Create demo account</Text></Pressable></View>;
    return <View><View style={styles.topRow}><View><Text style={styles.eyebrow}>CURRENT TRIP</Text><Text style={styles.title}>{group?.name || 'Loading…'}</Text><Text style={styles.muted}>{group?.destination || ''}</Text></View><View style={styles.steps}><Text style={styles.stepNumber}>{steps}</Text><Text style={styles.eyebrow}>STEPS</Text></View></View><View style={styles.page}><Text style={styles.pageLabel}>PAGE 01</Text><Text style={styles.pageTitle}>Little moments, kept close.</Text><Text style={styles.pageBody}>Your scrapbook is ready for photos, videos, notes, locations, and drawings from this trip.</Text><View style={styles.photoPlaceholder}><Text style={styles.photoText}>＋ Add a memory</Text></View></View></View>;
  };

  return <SafeAreaView style={styles.safe}><StatusBar style="dark"/><ScrollView contentContainerStyle={styles.container}><Text style={styles.brand}>timecapsule</Text>{renderContent()}</ScrollView><View style={styles.nav}>{['Groups','Record','Scrapbook','Calendar','Settings'].map(item => <Pressable key={item} onPress={() => setTab(item)} style={styles.navItem}><Text style={[styles.navText, tab === item && styles.navActive]}>{item}</Text></Pressable>)}</View></SafeAreaView>;
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#fbfaf7' }, container: { padding: 22, paddingBottom: 100 }, brand: { color: '#213c35', fontSize: 20, fontWeight: '700', marginBottom: 24 }, topRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 26 }, eyebrow: { color: '#9a8975', fontSize: 11, letterSpacing: 1.5, fontWeight: '700' }, title: { color: '#203b34', fontSize: 28, fontWeight: '800', marginTop: 4 }, heading: { color: '#203b34', fontSize: 25, fontWeight: '800', marginBottom: 16 }, muted: { color: '#796e63', fontSize: 14, lineHeight: 21 }, steps: { alignItems: 'flex-end' }, stepNumber: { color: '#db6d50', fontSize: 30, fontWeight: '800' }, page: { backgroundColor: '#f4eadb', minHeight: 470, borderRadius: 28, padding: 25, marginBottom: 20 }, pageLabel: { color: '#a58d71', fontSize: 11, letterSpacing: 2, fontWeight: '700' }, pageTitle: { color: '#253e36', fontSize: 34, lineHeight: 40, fontWeight: '800', marginTop: 80, maxWidth: 280 }, pageBody: { color: '#725f4d', fontSize: 16, lineHeight: 24, marginTop: 18, maxWidth: 300 }, photoPlaceholder: { backgroundColor: '#e6d4bc', borderRadius: 18, padding: 22, marginTop: 60, alignItems: 'center' }, photoText: { color: '#725f4d', fontWeight: '700' }, card: { backgroundColor: '#fff', borderRadius: 18, padding: 18, marginBottom: 12, borderWidth: 1, borderColor: '#eee6dd' }, cardTitle: { color: '#203b34', fontSize: 17, fontWeight: '700', marginBottom: 5 }, center: { alignItems: 'center', paddingTop: 80 }, recordIcon: { color: '#db6d50', fontSize: 64, marginBottom: 18 }, primary: { backgroundColor: '#203b34', paddingVertical: 15, paddingHorizontal: 22, borderRadius: 14, marginTop: 18 }, primaryText: { color: '#fff', fontWeight: '800' }, input: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#e6ded5', borderRadius: 13, padding: 15, marginBottom: 12, fontSize: 15 }, nav: { position: 'absolute', bottom: 0, left: 0, right: 0, backgroundColor: '#fff', borderTopWidth: 1, borderTopColor: '#eee6dd', flexDirection: 'row', justifyContent: 'space-around', paddingVertical: 16 }, navItem: { alignItems: 'center' }, navText: { color: '#9a8975', fontSize: 11, fontWeight: '700' }, navActive: { color: '#db6d50' }
});
