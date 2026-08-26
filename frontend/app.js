/**
 * VIGNAN — Adaptive Campus Intelligence Agent
 * Real Supabase Authentication & Profile Controller
 */

// --- Global Application State ---
const AppState = {
  supabase: null,
  user: null,
  authMode: 'signin', // 'signin' or 'signup'
  sessionId: 'session_' + Math.random().toString(36).substring(2, 10),
  isAudioEnabled: false,
  isRecording: false,
  recognition: null,
  directoryCache: {},
  currentModalTab: 'departments'
};

// Supabase Configuration (Client-side anon publishable key)
const SUPABASE_CONFIG = {
  url: 'https://nyndghsgfehcbfvlouoe.supabase.co',
  anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im55bmRnaHNnZmVoY2JmdmxvdW9lIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc3NDMzMTMsImV4cCI6MjEwMzMxOTMxM30.0vpZ9DCvmvd9mRKPGuBNOCkyftF08qWy4XYbks54bTA'
};

// ==========================================================================
// 1. INITIALIZATION & REAL SUPABASE AUTHENTICATION
// ==========================================================================
document.addEventListener('DOMContentLoaded', async () => {
  initSupabase();
  initVoiceRecognition();
  updateTimeGreeting();
  await checkAuthSession();
  checkBackendHealth();
  setupGlobalListeners();
});

/**
 * Initialize Supabase JS Client
 */
function initSupabase() {
  try {
    if (window.supabase && window.supabase.createClient) {
      AppState.supabase = window.supabase.createClient(SUPABASE_CONFIG.url, SUPABASE_CONFIG.anonKey);
      
      // Listen to real auth state changes
      AppState.supabase.auth.onAuthStateChange(async (event, session) => {
        if (event === 'SIGNED_IN' && session?.user) {
          await loadUserProfileAndDisplay(session.user);
        } else if (event === 'SIGNED_OUT') {
          showAuthView();
        }
      });
    }
  } catch (err) {
    console.error('Supabase JS initialization notice:', err);
  }
}

/**
 * Check if user is currently authenticated on page load
 */
async function checkAuthSession() {
  try {
    if (AppState.supabase) {
      const { data: { session }, error } = await AppState.supabase.auth.getSession();
      if (!error && session && session.user) {
        await loadUserProfileAndDisplay(session.user);
        return;
      }
    }
    // No active session -> display login view
    showAuthView();
  } catch (err) {
    console.warn('Session verification fallback:', err);
    showAuthView();
  }
}

/**
 * Fetch profile from `profiles` table in Supabase and display dashboard
 */
async function loadUserProfileAndDisplay(authUser) {
  if (!authUser) {
    showAuthView();
    return;
  }

  let profileData = null;

  try {
    if (AppState.supabase) {
      // Query the profiles table for this authenticated user ID
      const { data, error } = await AppState.supabase
        .from('profiles')
        .select('*')
        .eq('id', authUser.id)
        .maybeSingle();

      if (!error && data) {
        profileData = data;
      }
    }
  } catch (err) {
    console.warn('Profile fetch notice:', err);
  }

  // Derive profile fields dynamically (Never hardcoded)
  const metaFullName = authUser.user_metadata?.full_name || authUser.user_metadata?.name;
  const emailPrefix = (authUser.email || '').split('@')[0] || '';
  const cleanEmailPrefix = emailPrefix.replace(/[._-]/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

  const fullName = profileData?.full_name || metaFullName || cleanEmailPrefix || 'VIGNAN User';
  const firstName = fullName.split(' ')[0] || fullName;
  const email = profileData?.email || authUser.email || '';
  const avatarLetter = (firstName.charAt(0) || 'U').toUpperCase();

  AppState.user = {
    id: authUser.id,
    fullName: fullName,
    firstName: firstName,
    email: email,
    avatarLetter: avatarLetter,
    department: profileData?.department || '',
    year: profileData?.year || '',
    section: profileData?.section || '',
    studentId: profileData?.student_id || ''
  };

  showDashboardView(AppState.user);
}

/**
 * Switch UI to Authentication Screen
 */
function showAuthView() {
  AppState.user = null;
  
  const authContainer = document.getElementById('authContainer');
  const dashboardContainer = document.getElementById('dashboardContainer');
  const errorAlert = document.getElementById('authErrorAlert');

  if (errorAlert) {
    errorAlert.classList.remove('active');
    errorAlert.textContent = '';
  }

  // Reset form inputs (ensure always empty on open)
  const emailInput = document.getElementById('loginEmail');
  const pwdInput = document.getElementById('loginPassword');
  const nameInput = document.getElementById('regFullName');
  if (emailInput) emailInput.value = '';
  if (pwdInput) pwdInput.value = '';
  if (nameInput) nameInput.value = '';

  if (dashboardContainer) dashboardContainer.style.display = 'none';
  if (authContainer) authContainer.style.display = 'flex';
}

/**
 * Switch UI to Main Dashboard
 */
function showDashboardView(user) {
  const authContainer = document.getElementById('authContainer');
  const dashboardContainer = document.getElementById('dashboardContainer');

  if (authContainer) authContainer.style.display = 'none';
  if (dashboardContainer) dashboardContainer.style.display = 'flex';

  updateUserInterface(user);
}

/**
 * Update dynamic user elements with the real authenticated user's name
 */
function updateUserInterface(user) {
  if (!user) return;

  const headerName = document.getElementById('headerUserName');
  const headerAvatar = document.getElementById('headerAvatar');
  const dropdownName = document.getElementById('dropdownFullName');
  const dropdownEmail = document.getElementById('dropdownEmail');
  const dropdownAvatar = document.getElementById('dropdownAvatar');
  const heroName = document.getElementById('heroUserName');

  if (headerName) headerName.textContent = user.firstName;
  if (headerAvatar) headerAvatar.textContent = user.avatarLetter;
  if (dropdownName) dropdownName.textContent = user.fullName;
  if (dropdownEmail) dropdownEmail.textContent = user.email;
  if (dropdownAvatar) dropdownAvatar.textContent = user.avatarLetter;
  if (heroName) heroName.textContent = user.firstName;
}

/**
 * Toggle between Sign In mode and Sign Up (Create Account) mode
 */
function toggleAuthMode() {
  AppState.authMode = (AppState.authMode === 'signin') ? 'signup' : 'signin';
  
  const heading = document.getElementById('authHeading');
  const subheading = document.getElementById('authSubheading');
  const fullNameGroup = document.getElementById('fullNameGroup');
  const btnText = document.getElementById('authBtnText');
  const prompt = document.getElementById('authTogglePrompt');
  const toggleBtn = document.getElementById('authToggleBtn');
  const forgotBtn = document.getElementById('forgotPwdBtn');
  const errorAlert = document.getElementById('authErrorAlert');

  if (errorAlert) {
    errorAlert.classList.remove('active');
    errorAlert.textContent = '';
  }

  if (AppState.authMode === 'signup') {
    if (heading) heading.textContent = 'Create VIGNAN Account';
    if (subheading) subheading.textContent = 'Register with your university email to access the campus AI agent.';
    if (fullNameGroup) fullNameGroup.style.display = 'flex';
    if (btnText) btnText.textContent = 'Create Account';
    if (prompt) prompt.textContent = 'Already have an account?';
    if (toggleBtn) toggleBtn.textContent = 'Sign In';
    if (forgotBtn) forgotBtn.style.display = 'none';
  } else {
    if (heading) heading.textContent = 'Welcome Back';
    if (subheading) subheading.textContent = 'Sign in with your university account to access the verified VIGNAN AI assistant.';
    if (fullNameGroup) fullNameGroup.style.display = 'none';
    if (btnText) btnText.textContent = 'Sign In to VIGNAN';
    if (prompt) prompt.textContent = 'New to VIGNAN?';
    if (toggleBtn) toggleBtn.textContent = 'Create account';
    if (forgotBtn) forgotBtn.style.display = 'inline';
  }
}

/**
 * Handle Real Supabase Auth Form Submission (Sign In or Sign Up)
 */
async function handleAuthSubmit(event) {
  if (event) event.preventDefault();

  const emailInput = document.getElementById('loginEmail');
  const pwdInput = document.getElementById('loginPassword');
  const nameInput = document.getElementById('regFullName');
  const submitBtn = document.getElementById('authSubmitBtn');
  const btnText = document.getElementById('authBtnText');
  const errorAlert = document.getElementById('authErrorAlert');

  const email = emailInput ? emailInput.value.trim() : '';
  const password = pwdInput ? pwdInput.value : '';
  const fullName = nameInput ? nameInput.value.trim() : '';

  if (!email || !password) {
    showAuthError('Please enter both university email and password.');
    return;
  }

  if (AppState.authMode === 'signup' && !fullName) {
    showAuthError('Please enter your full name.');
    return;
  }

  // Set loading state
  if (submitBtn) submitBtn.classList.add('loading');
  if (btnText) btnText.textContent = AppState.authMode === 'signup' ? 'Creating account...' : 'Signing in...';
  if (errorAlert) errorAlert.classList.remove('active');

  try {
    if (!AppState.supabase) {
      throw new Error('Supabase client is initializing. Please try again.');
    }

    if (AppState.authMode === 'signup') {
      // 1. REAL SUPABASE SIGN UP
      const { data, error } = await AppState.supabase.auth.signUp({
        email: email,
        password: password,
        options: {
          data: {
            full_name: fullName
          }
        }
      });

      if (error) {
        throw error;
      }

      if (data?.session) {
        showToast('Account registered successfully! Signing in...', 'success');
        await loadUserProfileAndDisplay(data.user);
      } else if (data?.user) {
        // If Supabase requires email verification
        if (data.user.identities && data.user.identities.length === 0) {
          showAuthError('An account with this university email already exists. Please Sign In.');
        } else {
          showToast('Account created. Please check your email to verify before signing in.', 'info');
          setAuthMode('login');
        }
      } else {
        showToast('Account created. You may now sign in.', 'success');
        setAuthMode('login');
      }

    } else {
      // 2. REAL SUPABASE SIGN IN
      const { data, error } = await AppState.supabase.auth.signInWithPassword({
        email: email,
        password: password
      });

      if (error) {
        throw error;
      }

      if (data?.user) {
        await loadUserProfileAndDisplay(data.user);
        showToast(`Welcome back, ${AppState.user.firstName}!`, 'success');
      } else {
        throw new Error('Authentication succeeded but user session could not be established.');
      }
    }

  } catch (err) {
    console.error('Authentication error:', err);
    let msg = err.message || 'Invalid university credentials. Please check your email and password.';
    const lower = msg.toLowerCase();
    if (lower.includes('invalid login credentials')) {
      msg = 'Invalid credentials. Please verify your university email and password.';
    } else if (lower.includes('email not confirmed') || lower.includes('confirm your email') || lower.includes('unconfirmed')) {
      msg = 'Please verify your university email before signing in.';
    } else if (lower.includes('user already registered')) {
      msg = 'An account with this university email already exists. Please Sign In.';
    }
    showAuthError(msg);
  } finally {
    if (submitBtn) submitBtn.classList.remove('loading');
    if (btnText) btnText.textContent = AppState.authMode === 'signup' ? 'Create Account' : 'Sign In to VIGNAN';
  }
}

function showAuthError(message) {
  const errorAlert = document.getElementById('authErrorAlert');
  if (errorAlert) {
    errorAlert.textContent = message;
    errorAlert.classList.add('active');
  }
}

/**
 * Handle Logout via Supabase Auth
 */
async function handleLogout() {
  try {
    if (AppState.supabase) {
      await AppState.supabase.auth.signOut();
    }
  } catch (err) {
    console.warn('Sign out notice:', err);
  } finally {
    closeProfileDropdown();
    showAuthView();
    showToast('You have been signed out safely.', 'info');
  }
}

/**
 * Toggle Password Field Visibility
 */
function togglePasswordVisibility(fieldId, button) {
  const field = document.getElementById(fieldId);
  if (!field) return;

  if (field.type === 'password') {
    field.type = 'text';
    button.style.color = 'var(--accent-gold)';
  } else {
    field.type = 'password';
    button.style.color = 'var(--text-muted)';
  }
}

// ==========================================================================
// 2. FORGOT PASSWORD MODAL & FLOW
// ==========================================================================
function openForgotPasswordModal() {
  const modal = document.getElementById('forgotPasswordModal');
  const emailInput = document.getElementById('loginEmail');
  const resetEmail = document.getElementById('resetEmailInput');

  if (modal) modal.classList.add('active');
  if (resetEmail && emailInput && emailInput.value) {
    resetEmail.value = emailInput.value;
  }
}

function closeForgotPasswordModal() {
  const modal = document.getElementById('forgotPasswordModal');
  if (modal) modal.classList.remove('active');
}

function closeForgotPasswordOnBackdrop(event) {
  if (event.target.id === 'forgotPasswordModal') {
    closeForgotPasswordModal();
  }
}

async function handleForgotPasswordSubmit(event) {
  if (event) event.preventDefault();

  const resetEmailInput = document.getElementById('resetEmailInput');
  const submitBtn = document.getElementById('resetSubmitBtn');
  const btnText = document.getElementById('resetBtnText');

  const email = resetEmailInput ? resetEmailInput.value.trim() : '';
  if (!email) {
    showToast('Please enter your university email address.', 'warning');
    return;
  }

  if (submitBtn) submitBtn.classList.add('loading');
  if (btnText) btnText.textContent = 'Sending...';

  try {
    if (AppState.supabase) {
      const { error } = await AppState.supabase.auth.resetPasswordForEmail(email, {
        redirectTo: window.location.origin
      });

      if (error) throw error;

      closeForgotPasswordModal();
      showToast('Password reset link sent to your university email!', 'success');
    }
  } catch (err) {
    console.error('Password reset error:', err);
    showToast(err.message || 'Failed to send reset link. Please try again.', 'danger');
  } finally {
    if (submitBtn) submitBtn.classList.remove('loading');
    if (btnText) btnText.textContent = 'Send Reset Link';
  }
}

// ==========================================================================
// 3. TIME-AWARE GREETING & UI HELPERS
// ==========================================================================
function updateTimeGreeting() {
  const hour = new Date().getHours();
  let greeting = 'Good evening,';
  if (hour >= 4 && hour < 12) greeting = 'Good morning,';
  else if (hour >= 12 && hour < 17) greeting = 'Good afternoon,';

  const greetingEl = document.getElementById('greetingPrefix');
  if (greetingEl) greetingEl.textContent = greeting;
}

function toggleProfileDropdown(event) {
  if (event) event.stopPropagation();
  const wrapper = document.getElementById('userMenuWrapper');
  if (wrapper) wrapper.classList.toggle('active');
}

function closeProfileDropdown() {
  const wrapper = document.getElementById('userMenuWrapper');
  if (wrapper) wrapper.classList.remove('active');
}

function openProfileView(event) {
  if (event) event.preventDefault();
  closeProfileDropdown();
  showToast(`Profile: ${AppState.user?.fullName} (${AppState.user?.email})`, 'info');
}

function openSettingsView(event) {
  if (event) event.preventDefault();
  closeProfileDropdown();
  showToast('Settings: Voice Readout & Audio configured.', 'info');
}

function setupGlobalListeners() {
  document.addEventListener('click', (e) => {
    if (!e.target.closest('#userMenuWrapper')) {
      closeProfileDropdown();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeDirectoryModal();
      closeForgotPasswordModal();
      closeProfileDropdown();
    }
  });

  // Audio Toggle Button
  const audioBtn = document.getElementById('audioToggleBtn');
  if (audioBtn) {
    audioBtn.addEventListener('click', () => {
      AppState.isAudioEnabled = !AppState.isAudioEnabled;
      audioBtn.classList.toggle('active', AppState.isAudioEnabled);
      if (AppState.isAudioEnabled) {
        showToast('Voice readout enabled', 'success');
        speakText('Voice readout is now enabled.');
      } else {
        showToast('Voice readout muted', 'info');
      }
    });
  }
}

// ==========================================================================
// 4. AGENT QUERY & CHAT EXECUTION
// ==========================================================================
function executeQuickPrompt(text) {
  const input = document.getElementById('agentInput');
  if (input) {
    input.value = text;
    handleQuerySubmit(new Event('submit'));
  }
}

async function handleQuerySubmit(event) {
  if (event) event.preventDefault();

  const input = document.getElementById('agentInput');
  if (!input) return;

  const query = input.value.trim();
  if (!query) return;

  // Clear input
  input.value = '';

  // 1. Append User Message
  appendUserMessage(query);

  // 2. Set Floating Agent to "Thinking" State
  setFloatingAgentState(true);

  // 3. Add Skeleton Loading Placeholder Bubble
  const loadingBubbleId = appendLoadingSkeleton();

  // Check if query is requesting user device location
  let messagePayload = query;
  if (/where i am|my location|my current location|from here/i.test(query)) {
    if (navigator.geolocation) {
      try {
        const pos = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 4000 });
        });
        if (pos && pos.coords) {
          messagePayload += ` (from coordinates: ${pos.coords.latitude.toFixed(6)}, ${pos.coords.longitude.toFixed(6)})`;
          showToast('Using device coordinates for navigation.', 'info');
        }
      } catch (geoErr) {
        console.warn('Geolocation permission not granted:', geoErr);
        showToast('Device location access denied. Please specify your starting block.', 'warning');
      }
    }
  }

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: messagePayload,
        session_id: AppState.sessionId,
        user: {
          name: AppState.user?.fullName || 'Student',
          full_name: AppState.user?.fullName || 'Student',
          email: AppState.user?.email || 'student@vignan.ac.in',
          year: AppState.user?.year || '',
          section: AppState.user?.section || '',
          department: AppState.user?.department || '',
          student_id: AppState.user?.studentId || ''
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}`);
    }

    const data = await response.json();

    // 4. Replace Loading Skeleton with formatted Assistant Response
    replaceSkeletonWithResponse(loadingBubbleId, data);

    // 5. Speak response if Audio is enabled
    if (AppState.isAudioEnabled && data.answer) {
      speakText(cleanTextForSpeech(data.answer));
    }
  } catch (err) {
    console.error('Chat query error:', err);
    replaceSkeletonWithResponse(loadingBubbleId, {
      answer: "I apologize, but I encountered a network issue reaching the campus coordinator. Please verify your connection or try asking again.",
      confidence: "low",
      verified: false,
      provenance: []
    });
  } finally {
    // Return Floating Agent to Idle
    setFloatingAgentState(false);
  }
}

/**
 * Append User Message Bubble
 */
function appendUserMessage(text) {
  const container = document.getElementById('chatConversationArea');
  if (!container) return;

  const userInitial = AppState.user?.avatarLetter || 'U';
  const timeStr = formatCurrentTime();

  const msgDiv = document.createElement('div');
  msgDiv.className = 'chat-message message-user';
  msgDiv.innerHTML = `
    <div class="msg-avatar">${escapeHtml(userInitial)}</div>
    <div class="msg-content-wrapper">
      <div class="msg-sender-name">${escapeHtml(AppState.user?.firstName || 'You')}</div>
      <div class="msg-bubble">${escapeHtml(text)}</div>
      <div class="msg-footer-actions">
        <span class="msg-timestamp">${timeStr}</span>
      </div>
    </div>
  `;

  container.appendChild(msgDiv);
  scrollConversationToBottom();
}

/**
 * Append Loading Skeleton Placeholder
 */
function appendLoadingSkeleton() {
  const container = document.getElementById('chatConversationArea');
  if (!container) return null;

  const skeletonId = 'skeleton_' + Date.now();
  const msgDiv = document.createElement('div');
  msgDiv.className = 'chat-message message-assistant';
  msgDiv.id = skeletonId;
  msgDiv.innerHTML = `
    <div class="msg-avatar">
      <img src="/assets/logo.svg" alt="VIGNAN" width="16" height="16">
    </div>
    <div class="msg-content-wrapper" style="min-width: 220px;">
      <div class="msg-sender-name">VIGNAN Assistant</div>
      <div class="msg-bubble">
        <div class="loading-skeleton-pulse">
          <div class="skeleton-line" style="width: 75%;"></div>
          <div class="skeleton-line" style="width: 90%;"></div>
          <div class="skeleton-line" style="width: 60%;"></div>
        </div>
      </div>
    </div>
  `;

  container.appendChild(msgDiv);
  scrollConversationToBottom();
  return skeletonId;
}

/**
 * Replace Skeleton with formatted Assistant Response
 */
function replaceSkeletonWithResponse(skeletonId, data) {
  const skeletonEl = document.getElementById(skeletonId);
  if (!skeletonEl) return;

  const formattedHtml = formatAgentAnswer(data.answer || '');
  const metadataTagsHtml = renderMetadataPills(data);
  const navigationCardHtml = renderNavigationCard(data.route);
  const timeStr = formatCurrentTime();
  const answerId = 'ans_' + Math.random().toString(36).substring(2, 8);

  skeletonEl.innerHTML = `
    <div class="msg-avatar">
      <img src="/assets/logo.svg" alt="VIGNAN" width="16" height="16">
    </div>
    <div class="msg-content-wrapper">
      <div class="msg-sender-name">VIGNAN Assistant</div>
      <div class="msg-bubble">
        <div class="msg-text-body" id="${answerId}">${formattedHtml}</div>
        ${navigationCardHtml}
        ${metadataTagsHtml}
      </div>
      <div class="msg-footer-actions">
        <span class="msg-timestamp">${timeStr}</span>
        <div class="msg-tools-group">
          <button type="button" class="msg-action-btn" onclick="speakMessage('${answerId}')" title="Listen to response">
            <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"/></svg>
            Speak
          </button>
          <button type="button" class="msg-action-btn" onclick="recordFeedback(this, 1)" title="Helpful answer">
            <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"/></svg>
            Helpful
          </button>
        </div>
      </div>
    </div>
  `;

  scrollConversationToBottom();
}

/**
 * Render Google Maps Navigation Route Card
 */
function renderNavigationCard(route) {
  if (!route || !route.google_maps_url) return '';

  const origin = escapeHtml(route.origin || route.start_location || 'Main Gate');
  const destination = escapeHtml(route.destination || route.destination_location || 'Destination');
  const travelMode = escapeHtml((route.travel_mode || 'Walking').toUpperCase());
  const estMins = route.estimated_minutes ? `${route.estimated_minutes} mins` : '';
  const indoorGuidance = route.indoor_guidance ? `<div class="route-indoor-note"><strong>Indoor Guidance:</strong> ${escapeHtml(route.indoor_guidance)}</div>` : '';
  
  let embeddedMapHtml = '';
  if (route.embedded_map_available && route.embedded_map_url) {
    embeddedMapHtml = `
      <div class="embedded-map-container">
        <iframe
          width="100%"
          height="180"
          style="border:0; border-radius: 8px; margin-top: 8px;"
          loading="lazy"
          allowfullscreen
          src="${escapeHtml(route.embedded_map_url)}">
        </iframe>
      </div>
    `;
  }

  return `
    <div class="navigation-route-card">
      <div class="route-header">
        <div class="route-badge">
          <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"/></svg>
          ${travelMode} ${estMins ? '· ~' + estMins : ''}
        </div>
      </div>
      <div class="route-endpoints">
        <div class="route-point from">
          <span class="dot"></span>
          <span class="label">From:</span>
          <span class="val">${origin}</span>
        </div>
        <div class="route-point to">
          <span class="dot"></span>
          <span class="label">To:</span>
          <span class="val">${destination}</span>
        </div>
      </div>
      ${indoorGuidance}
      ${embeddedMapHtml}
      <div class="route-actions">
        <a href="${escapeHtml(route.google_maps_url)}" target="_blank" rel="noopener noreferrer" class="btn-open-maps">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>
          Open in Google Maps
        </a>
      </div>
    </div>
  `;
}

/**
 * Format markdown and paragraphs
 */
function formatAgentAnswer(rawText) {
  if (!rawText) return '';

  let html = rawText
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code style="background: #f1ede4; padding: 2px 5px; border-radius: 4px; font-size: 0.8em;">$1</code>');

  const lines = html.split('\n');
  let output = '';
  let inList = false;

  for (let line of lines) {
    line = line.trim();
    if (line.startsWith('- ') || line.startsWith('• ') || line.startsWith('* ')) {
      if (!inList) {
        output += '<ul style="margin: 0.35rem 0; padding-left: 1.25rem; font-size: 0.84rem;">';
        inList = true;
      }
      output += `<li style="margin-bottom: 0.2rem;">${line.substring(2)}</li>`;
    } else {
      if (inList) {
        output += '</ul>';
        inList = false;
      }
      if (line) {
        output += `<p style="margin-bottom: 0.35rem;">${line}</p>`;
      }
    }
  }

  if (inList) output += '</ul>';
  return output || `<p>${escapeHtml(rawText)}</p>`;
}

/**
 * Render compact metadata pills
 */
function renderMetadataPills(data) {
  const pills = [];

  // 1. Location Pill
  if (data.block || data.floor || data.room) {
    const locParts = [data.block, data.floor, data.room].filter(Boolean);
    pills.push(`
      <span class="meta-pill location">
        <svg width="10" height="10" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"/></svg>
        ${escapeHtml(locParts.join(' · '))}
      </span>
    `);
  }

  // 2. Verified Pill
  if (data.verified !== false && data.confidence !== 'low') {
    pills.push(`
      <span class="meta-pill verified">
        <svg width="10" height="10" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>
        Verified
      </span>
    `);
  }

  // 3. Source Pill
  if (data.provenance && data.provenance.length > 0) {
    const srcName = data.provenance[0].source_name || 'VIGNAN Registry';
    pills.push(`
      <span class="meta-pill source">
        Source: ${escapeHtml(srcName)}
      </span>
    `);
  }

  // 4. Live Status Pill
  if (data.is_open !== undefined) {
    const isOpen = data.is_open;
    pills.push(`
      <span class="meta-pill live-status" style="background-color: ${isOpen ? '#ecfdf5' : '#fef2f2'}; color: ${isOpen ? '#059669' : '#dc2626'}; border-color: ${isOpen ? '#a7f3d0' : '#fecaca'};">
        ● ${isOpen ? 'Open Now' : 'Closed'}
      </span>
    `);
  }

  if (pills.length === 0) return '';
  return `<div class="msg-metadata-tags">${pills.join('')}</div>`;
}

/**
 * Scroll conversation area internally
 */
function scrollConversationToBottom() {
  const container = document.getElementById('chatConversationArea');
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
}

/**
 * Clear Chat History
 */
function clearChatHistory() {
  const container = document.getElementById('chatConversationArea');
  if (!container) return;

  container.innerHTML = `
    <div class="chat-message message-assistant" id="initialWelcomeMessage">
      <div class="msg-avatar">
        <img src="/assets/logo.svg" alt="VIGNAN" width="16" height="16">
      </div>
      <div class="msg-content-wrapper">
        <div class="msg-sender-name">VIGNAN Campus Assistant</div>
        <div class="msg-bubble">
          <p>Conversation history cleared. How may I assist you with VIGNAN campus today?</p>
        </div>
      </div>
    </div>
  `;
  showToast('Chat history cleared', 'info');
}

// ==========================================================================
// 5. FLOATING AGENT THINKING BADGE
// ==========================================================================
function setFloatingAgentState(isThinking) {
  const badge = document.getElementById('floatingAgentBadge');
  const label = document.getElementById('floatingAgentLabel');
  if (!badge || !label) return;

  if (isThinking) {
    badge.classList.add('is-thinking');
    label.textContent = 'VIGNAN is thinking...';
  } else {
    badge.classList.remove('is-thinking');
    label.textContent = 'VIGNAN Online';
  }
}

// ==========================================================================
// 6. VOICE & SPEECH SYNTHESIS
// ==========================================================================
function initVoiceRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;

  AppState.recognition = new SpeechRecognition();
  AppState.recognition.continuous = false;
  AppState.recognition.interimResults = false;
  AppState.recognition.lang = 'en-IN';

  AppState.recognition.onstart = () => {
    AppState.isRecording = true;
    updateVoiceUI(true);
  };

  AppState.recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    const input = document.getElementById('agentInput');
    if (input && transcript) {
      input.value = transcript;
      handleQuerySubmit(new Event('submit'));
    }
  };

  AppState.recognition.onerror = (event) => {
    console.warn('Speech recognition notice:', event.error);
    AppState.isRecording = false;
    updateVoiceUI(false);
  };

  AppState.recognition.onend = () => {
    AppState.isRecording = false;
    updateVoiceUI(false);
  };
}

function toggleVoiceRecording() {
  if (!AppState.recognition) {
    showToast('Voice input is not supported in this browser. Please use Chrome/Edge.', 'warning');
    return;
  }

  if (AppState.isRecording) {
    AppState.recognition.stop();
  } else {
    try {
      AppState.recognition.start();
    } catch (e) {
      console.warn('Voice start notice:', e);
    }
  }
}

function updateVoiceUI(isRecording) {
  const voiceBtn = document.getElementById('voiceBtn');
  const waveIndicator = document.getElementById('voiceWaveIndicator');

  if (voiceBtn) voiceBtn.classList.toggle('recording', isRecording);
  if (waveIndicator) waveIndicator.classList.toggle('active', isRecording);
}

function speakMessage(bodyId) {
  const el = document.getElementById(bodyId);
  if (el) {
    speakText(cleanTextForSpeech(el.innerText || el.textContent));
  }
}

function speakText(text) {
  if (!window.speechSynthesis || !text) return;
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  utterance.lang = 'en-IN';
  window.speechSynthesis.speak(utterance);
}

function cleanTextForSpeech(text) {
  return text
    .replace(/[*_#`]/g, '')
    .replace(/\[.*?\]/g, '')
    .replace(/https?:\/\/\S+/g, '')
    .trim();
}

// ==========================================================================
// 7. FEEDBACK RECORDING
// ==========================================================================
async function recordFeedback(buttonEl, rating) {
  if (buttonEl.classList.contains('active')) return;

  try {
    buttonEl.classList.add('active');
    buttonEl.innerHTML = `
      <svg width="12" height="12" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
      Thanks!
    `;

    await fetch('/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: AppState.sessionId,
        rating: rating,
        category: 'accuracy'
      })
    });
    showToast('Feedback recorded. Thank you!', 'success');
  } catch (err) {
    console.warn('Feedback notice:', err);
  }
}

// ==========================================================================
// 8. CAMPUS DIRECTORY MODAL
// ==========================================================================
async function openDirectoryModal(category = 'departments') {
  const modal = document.getElementById('directoryModal');
  if (!modal) return;

  modal.classList.add('active');
  switchDirectoryTab(category);
}

function closeDirectoryModal() {
  const modal = document.getElementById('directoryModal');
  if (modal) modal.classList.remove('active');
}

function closeDirectoryModalOnBackdrop(event) {
  if (event.target.id === 'directoryModal') {
    closeDirectoryModal();
  }
}

async function switchDirectoryTab(category) {
  AppState.currentModalTab = category;

  const tabs = {
    departments: 'tabDept',
    faculty: 'tabFaculty',
    services: 'tabServices',
    academic_support: 'tabAcademicSupport'
  };

  Object.entries(tabs).forEach(([cat, tabId]) => {
    const btn = document.getElementById(tabId);
    if (btn) btn.classList.toggle('active', cat === category);
  });

  const grid = document.getElementById('directoryGridContainer');
  if (!grid) return;

  grid.innerHTML = `
    <div class="loading-skeleton-pulse">
      <div class="skeleton-line" style="width: 70%;"></div>
      <div class="skeleton-line" style="width: 90%;"></div>
      <div class="skeleton-line" style="width: 80%;"></div>
    </div>
  `;

  if (AppState.directoryCache[category]) {
    renderDirectoryItems(AppState.directoryCache[category], category);
  } else {
    try {
      const res = await fetch(`/directory?category=${category}`);
      const json = await res.json();
      AppState.directoryCache[category] = json.data || [];
      renderDirectoryItems(AppState.directoryCache[category], category);
    } catch (err) {
      grid.innerHTML = `<p style="color: var(--status-danger); font-size: 0.8125rem;">Failed to load directory items.</p>`;
    }
  }
}

function renderDirectoryItems(items, category = AppState.currentModalTab) {
  const grid = document.getElementById('directoryGridContainer');
  if (!grid) return;

  if (!items || items.length === 0) {
    grid.innerHTML = `<p style="color: var(--text-muted); font-size: 0.875rem; grid-column: 1 / -1; padding: 2rem 1rem; text-align: center;">No verified records found matching your filter.</p>`;
    return;
  }

  if (category === 'faculty') {
    grid.innerHTML = items.map(f => {
      const name = f.full_name || f.name || 'Faculty Member';
      const desig = f.designation || '';
      const dept = f.department_name || '';
      const room = f.room ? `Room: ${f.room}` : '';
      const block = f.block ? f.block : '';
      const floor = f.floor ? f.floor : '';
      const locBadge = [room, block, floor].filter(Boolean).join(' • ');
      const email = f.email ? f.email : '';
      const phone = f.phone ? f.phone : '';

      return `
        <div class="directory-card" onclick="askAboutDirectoryItem('${escapeHtml(name)}')">
          <div class="dir-header">
            <span class="dir-title">${escapeHtml(name)}</span>
            ${desig ? `<span class="dir-role">${escapeHtml(desig)}</span>` : ''}
          </div>
          ${dept ? `<span class="dir-dept">${escapeHtml(dept)}</span>` : ''}
          ${locBadge ? `<div class="dir-badge"><svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/></svg> ${escapeHtml(locBadge)}</div>` : ''}
          <div class="dir-contacts">
            ${email ? `<span class="dir-contact-item"><svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg> ${escapeHtml(email)}</span>` : ''}
            ${phone ? `<span class="dir-contact-item"><svg width="11" height="11" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/></svg> ${escapeHtml(phone)}</span>` : ''}
          </div>
        </div>
      `;
    }).join('');
  } else if (category === 'departments') {
    grid.innerHTML = items.map(d => {
      const name = d.name || 'Academic Department';
      const code = d.short_name || '';
      const block = d.block ? d.block : '';
      const floor = d.floor_information ? d.floor_information : '';
      const locInfo = [block, floor].filter(Boolean).join(' • ');
      const hodName = d.hod?.full_name ? `HOD: ${d.hod.full_name}` : '';

      return `
        <div class="directory-card" onclick="askAboutDirectoryItem('${escapeHtml(name)}')">
          <div class="dir-header">
            <span class="dir-title">${escapeHtml(name)}</span>
            ${code ? `<span class="dir-code-tag">${escapeHtml(code)}</span>` : ''}
          </div>
          ${hodName ? `<span class="dir-hod">${escapeHtml(hodName)}</span>` : ''}
          ${locInfo ? `<div class="dir-badge"><svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg> ${escapeHtml(locInfo)}</div>` : ''}
        </div>
      `;
    }).join('');
  } else if (category === 'services') {
    grid.innerHTML = items.map(s => {
      const name = s.name || 'Campus Service';
      const cat = s.category ? s.category.toUpperCase() : 'FACILITY';
      const loc = typeof s.location === 'object' ? (s.location?.description || s.location?.name || s.description || 'Campus') : (s.location || s.description || 'Campus');
      const desc = s.description || '';
      const svcs = Array.isArray(s.services_offered) ? s.services_offered : [];

      return `
        <div class="directory-card" onclick="askAboutDirectoryItem('${escapeHtml(name)}')">
          <div class="dir-header">
            <span class="dir-title">${escapeHtml(name)}</span>
            <span class="dir-category-tag">${escapeHtml(cat)}</span>
          </div>
          ${desc ? `<p class="dir-desc">${escapeHtml(desc)}</p>` : ''}
          ${loc ? `<div class="dir-badge"><svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/></svg> ${escapeHtml(loc)}</div>` : ''}
          ${svcs.length > 0 ? `
            <div class="dir-tags-row">
              ${svcs.slice(0, 3).map(svc => `<span class="dir-pill">${escapeHtml(svc)}</span>`).join('')}
            </div>
          ` : ''}
        </div>
      `;
    }).join('');
  } else if (category === 'academic_support') {
    grid.innerHTML = items.map(a => {
      const name = a.person_name || 'Academic Lead';
      const role = a.role_name || a.role || '';
      const resp = a.responsibilities || '';
      const phone = a.phone ? `Phone: ${a.phone}` : '';
      const room = a.room ? `Room: ${a.room}` : '';
      const email = a.email ? a.email : '';
      const meta = [room, phone].filter(Boolean).join(' • ');

      return `
        <div class="directory-card" onclick="askAboutDirectoryItem('${escapeHtml(name)}')">
          <div class="dir-header">
            <span class="dir-title">${escapeHtml(name)}</span>
            ${role ? `<span class="dir-role">${escapeHtml(role)}</span>` : ''}
          </div>
          ${resp ? `<p class="dir-desc" title="${escapeHtml(resp)}">${escapeHtml(resp)}</p>` : ''}
          ${meta ? `<div class="dir-badge"><svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg> ${escapeHtml(meta)}</div>` : ''}
          ${email ? `<div class="dir-contacts"><span class="dir-contact-item">${escapeHtml(email)}</span></div>` : ''}
        </div>
      `;
    }).join('');
  }
}

function filterDirectoryRecords(query) {
  const q = query.toLowerCase().trim();
  const currentCategory = AppState.currentModalTab || 'departments';
  const currentList = AppState.directoryCache[currentCategory] || [];
  if (!q) {
    renderDirectoryItems(currentList, currentCategory);
    return;
  }

  const filtered = currentList.filter(item => {
    const searchTargets = [
      item.full_name,
      item.person_name,
      item.name,
      item.short_name,
      item.designation,
      item.role_name,
      item.department_name,
      item.email,
      item.phone,
      item.room,
      item.block,
      item.description,
      item.hod?.full_name,
      Array.isArray(item.services_offered) ? item.services_offered.join(' ') : ''
    ].filter(Boolean).map(s => String(s).toLowerCase());

    return searchTargets.some(target => target.includes(q));
  });

  renderDirectoryItems(filtered, currentCategory);
}

function askAboutDirectoryItem(name) {
  closeDirectoryModal();
  executeQuickPrompt(`Where is ${name}?`);
}

// ==========================================================================
// 9. BACKEND HEALTH CHECK & UTILS
// ==========================================================================
async function checkBackendHealth() {
  const statusPill = document.getElementById('backendStatusPill');
  const statusText = document.getElementById('backendStatusText');

  try {
    const res = await fetch('/health');
    if (res.ok) {
      if (statusPill) statusPill.style.display = 'inline-flex';
      if (statusText) statusText.textContent = 'Agent Online';
    }
  } catch (err) {
    if (statusText) statusText.textContent = 'Agent Offline';
  }
}

function formatCurrentTime() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'toast-msg';
  if (type === 'success') toast.style.backgroundColor = 'var(--status-success)';
  if (type === 'warning') toast.style.backgroundColor = 'var(--status-warning)';
  if (type === 'danger') toast.style.backgroundColor = 'var(--status-danger)';
  toast.textContent = message;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
