import { BehaviorSubject, Observable } from 'rxjs';

export class ResponsiveCheckHelper {
  private currentScreen: number = 0;
  isResponsive: boolean = false;
  private responsiveSubject: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(this.isResponsive);
  private changeDisplaySubject: BehaviorSubject<boolean> = new BehaviorSubject<any>({width: window.innerWidth, height: window.innerHeight, isResponsive: this.isResponsive});

  constructor() {
    window.addEventListener('resize', ()=>{
      this.checkResponsive.bind(this)
    }); // Asigna correctamente el contexto a la función
    this.checkResponsive(); // Llama a la función inicialmente para comprobar el estado actual
  }

  // Función para obtener el observable del estado de isResponsive
  getResponsiveStatus(): Observable<boolean> {
    return this.responsiveSubject.asObservable();
  }
  changeDisplay(): Observable<any> {
    return this.changeDisplaySubject.asObservable();
  }

  checkResponsive() {
    if (this.currentScreen !== window.innerWidth) {
      if ((window.innerWidth < 993) || this.isMobileDevice()) {
        this.isResponsive = true;
      } else {
        this.isResponsive = false;
      }
      this.currentScreen = window.innerWidth; // Actualizamos la pantalla
      this.responsiveSubject.next(this.isResponsive); // Emitimos el nuevo estado
    }
    this.changeDisplaySubject.next({width: window.innerWidth, height: window.innerHeight, isResponsive: this.isResponsive} as any)
    return this.isResponsive
  }

  private isMobileDevice() {
    // Detección de dispositivos móviles excluyendo iPad y tabletas Android
    return /Android(?!.*(Tablet|tab|SCH-I800|SGH-T849|SPH-P100|SGH-T849|SHW-M180S|SHW-M180W))|webOS|iPhone|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|mobile|Touch|Windows Phone|HarmonyOS/i.test(navigator.userAgent) &&
      !/iPad|Tablet/i.test(navigator.userAgent);
  }
}
