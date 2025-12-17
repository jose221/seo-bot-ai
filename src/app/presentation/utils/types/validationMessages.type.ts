export type ValidationMessageOptions = {
  /**
   * Controla cuándo mostrar:
   * - 'touchedOrDirty': (default) touched || dirty
   * - 'always': siempre que haya errors
   * - 'submitted': muestra si submitted=true
   */
  mode?: 'touchedOrDirty' | 'always' | 'submitted';
  submitted?: boolean;

  /**
   * Prefijo de keys, por defecto "validation".
   * Ej: validation.required, validation.email...
   */
  keyPrefix?: string;

  /**
   * Nombre "humano" del campo para interpolar en traducciones.
   * Ej: "Email" -> "El campo {{field}} es obligatorio"
   */
  fieldLabel?: string;

  /**
   * Override por campo y error:
   * {
   *   email: { required: 'auth.emailRequired', email: 'auth.emailInvalid' }
   * }
   */
  fieldErrorKeys?: Record<string, Record<string, string>>;

  /**
   * Forzar orden de errores (si quieres que required salga primero, etc.)
   */
  errorPriority?: string[];
};
