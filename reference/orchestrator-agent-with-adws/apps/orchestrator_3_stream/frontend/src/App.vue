<template>
  <div class="app-container">
    <AppHeader />

    <main class="app-main"
          :class="{
            'sidebar-collapsed': isSidebarCollapsed,
            'chat-md': store.chatWidth === 'md',
            'chat-lg': store.chatWidth === 'lg'
          }">
      <AgentList
        class="app-sidebar left"
        :agents="store.agents"
        :selected-agent-id="store.selectedAgentId"
        @select-agent="handleSelectAgent"
        @add-agent="handleAddAgent"
        @collapse-change="handleSidebarCollapse"
      />

      <!-- Center Column: EventStream or AdwSwimlanes based on view mode -->
      <EventStream
        v-if="store.viewMode === 'logs'"
        ref="eventStreamRef"
        class="app-content center"
        :events="store.filteredEventStream"
        :current-filter="store.eventStreamFilter"
        :auto-scroll="true"
        @set-filter="handleSetFilter"
      />
      <AdwSwimlanes
        v-else
        class="app-content center"
      />

      <OrchestratorChat
        class="app-sidebar right"
        :messages="store.chatMessages"
        :is-connected="store.isConnected"
        :is-typing="store.isTyping"
        :auto-scroll="store.autoScroll"
        @send="handleSendMessage"
      />
    </main>

    <!-- Global Command Input -->
    <GlobalCommandInput
      :visible="store.commandInputVisible"
      @send="handleSendMessage"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import AppHeader from './components/AppHeader.vue'
import AgentList from './components/AgentList.vue'
import EventStream from './components/EventStream.vue'
import AdwSwimlanes from './components/AdwSwimlanes.vue'
import OrchestratorChat from './components/OrchestratorChat.vue'
import GlobalCommandInput from './components/GlobalCommandInput.vue'
import { useOrchestratorStore } from './stores/orchestratorStore'
import { useKeyboardShortcuts } from './composables/useKeyboardShortcuts'

// Use Pinia store
const store = useOrchestratorStore()

// Initialize keyboard shortcuts
useKeyboardShortcuts()

// Component refs
const eventStreamRef = ref<InstanceType<typeof EventStream> | null>(null)

// Sidebar collapse state
const isSidebarCollapsed = ref(false)

// Initialize store on mount
onMounted(() => {
  store.initialize()
})

// Clean up on unmount to prevent duplicate connections during HMR
onUnmounted(() => {
  store.disconnectWebSocket()
})

// Handlers
const handleSelectAgent = (id: string) => {
  store.selectAgent(id)

  // Toggle agent filter in EventStream
  const agent = store.agents.find(a => a.id === id)
  if (agent && eventStreamRef.value) {
    eventStreamRef.value.toggleAgentFilter(agent.name)
  }
}

const handleAddAgent = () => {
  console.log('Add agent clicked')
  // TODO: Open modal to create new agent
}

const handleSetFilter = (filter: string) => {
  store.setEventStreamFilter(filter as any)
}

const handleSendMessage = (message: string) => {
  store.sendUserMessage(message)
}

const handleSidebarCollapse = (isCollapsed: boolean) => {
  isSidebarCollapsed.value = isCollapsed
}
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Main Layout */
.app-main {
  flex: 1;
  display: grid;
  grid-template-columns: 280px 1fr 418px;
  overflow: hidden;
  transition: grid-template-columns 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Chat width variations */
.app-main.chat-md {
  grid-template-columns: 280px 1fr 518px;
}

.app-main.chat-lg {
  grid-template-columns: 280px 1fr 618px;
}

/* Combined with sidebar collapsed */
.app-main.sidebar-collapsed {
  grid-template-columns: 48px 1fr 418px;
}

.app-main.sidebar-collapsed.chat-md {
  grid-template-columns: 48px 1fr 518px;
}

.app-main.sidebar-collapsed.chat-lg {
  grid-template-columns: 48px 1fr 618px;
}

.app-sidebar,
.app-content {
  height: 100%;
  overflow: hidden;
}

/* Responsive */
@media (max-width: 1600px) {
  /* Limit large size on smaller screens */
  .app-main.chat-lg {
    grid-template-columns: 280px 1fr 518px; /* Fall back to medium */
  }

  .app-main.sidebar-collapsed.chat-lg {
    grid-template-columns: 48px 1fr 518px;
  }
}

@media (max-width: 1400px) {
  .app-main {
    grid-template-columns: 260px 1fr 385px;
  }

  .app-main.chat-md {
    grid-template-columns: 260px 1fr 450px; /* Reduced increase */
  }

  .app-main.chat-lg {
    grid-template-columns: 260px 1fr 450px; /* Cap at medium */
  }

  .app-main.sidebar-collapsed {
    grid-template-columns: 48px 1fr 385px;
  }

  .app-main.sidebar-collapsed.chat-md {
    grid-template-columns: 48px 1fr 450px;
  }

  .app-main.sidebar-collapsed.chat-lg {
    grid-template-columns: 48px 1fr 450px;
  }
}

@media (max-width: 1200px) {
  /* Force small size on narrow screens */
  .app-main,
  .app-main.chat-md,
  .app-main.chat-lg {
    grid-template-columns: 240px 1fr 352px;
  }

  .app-main.sidebar-collapsed,
  .app-main.sidebar-collapsed.chat-md,
  .app-main.sidebar-collapsed.chat-lg {
    grid-template-columns: 48px 1fr 352px;
  }
}

@media (max-width: 1024px) {
  .app-main,
  .app-main.chat-md,
  .app-main.chat-lg {
    grid-template-columns: 220px 1fr 330px;
  }

  .app-main.sidebar-collapsed,
  .app-main.sidebar-collapsed.chat-md,
  .app-main.sidebar-collapsed.chat-lg {
    grid-template-columns: 48px 1fr 330px;
  }
}

/* Mobile Responsive Design (< 650px) */
@media (max-width: 650px) {
  /* Force 3-column layout with collapsed sidebars */
  .app-main,
  .app-main.chat-md,
  .app-main.chat-lg,
  .app-main.sidebar-collapsed,
  .app-main.sidebar-collapsed.chat-md,
  .app-main.sidebar-collapsed.chat-lg {
    grid-template-columns: 48px 1fr 280px;
  }

  /* Force AgentList to always be collapsed on mobile */
  .app-sidebar.left {
    width: 48px !important;
    min-width: 48px !important;
  }

  /* OrchestratorChat small mode on mobile */
  .app-sidebar.right {
    width: 280px !important;
    min-width: 280px !important;
  }
}

/* Very narrow mobile devices - hide chat for more event space */
@media (max-width: 400px) {
  .app-main,
  .app-main.chat-md,
  .app-main.chat-lg,
  .app-main.sidebar-collapsed,
  .app-main.sidebar-collapsed.chat-md,
  .app-main.sidebar-collapsed.chat-lg {
    grid-template-columns: 48px 1fr 0;
  }

  .app-sidebar.right {
    display: none;
  }
}
</style>
