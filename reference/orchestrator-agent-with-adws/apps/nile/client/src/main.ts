import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';
import { useUserStore } from './stores/user';
import './style.css';

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);

// Restore user session before mounting
const userStore = useUserStore();
userStore.restoreSession();

app.use(router);
app.mount('#app');
