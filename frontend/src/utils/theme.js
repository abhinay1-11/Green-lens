export function getThemePreference() {
  return localStorage.getItem('greenlens-theme') || 'dark';
}

export function getResolvedTheme(preference) {
  if (preference === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return preference === 'light' ? 'light' : 'dark';
}

export function applyTheme(preference) {
  const resolved = getResolvedTheme(preference);
  document.documentElement.setAttribute('data-theme', resolved);
  localStorage.setItem('greenlens-theme', preference);
  return resolved;
}

export function initTheme(onChangeCallback) {
  const preference = getThemePreference();
  applyTheme(preference);

  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  const handleSystemChange = () => {
    const currentPref = getThemePreference();
    if (currentPref === 'system') {
      const resolved = applyTheme('system');
      if (onChangeCallback) onChangeCallback('system', resolved);
    }
  };

  if (mediaQuery.addEventListener) {
    mediaQuery.addEventListener('change', handleSystemChange);
  } else {
    mediaQuery.addListener(handleSystemChange);
  }

  return () => {
    if (mediaQuery.removeEventListener) {
      mediaQuery.removeEventListener('change', handleSystemChange);
    } else {
      mediaQuery.removeListener(handleSystemChange);
    }
  };
}
