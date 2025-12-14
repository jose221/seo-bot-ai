import * as bootstrap from "bootstrap";

interface ModalOptions {
  centered?: boolean;
  scrollable?: boolean;
  size?: 'sm' | 'lg' | 'xl';
  modalBody?: string | string[];
  modalFooter?: string;
  modalHeader?: string;
  fullscreenMdDown?: boolean;
  overflowElement?: string;
}


export class BootstrapModal {
  private modalElement: HTMLElement | null | any;
  private bootstrapModal: any;

  constructor(modalId: string, instancia: boolean = true) {
    this.modalElement = document.querySelector(modalId);

    if (!this.modalElement) {
      throw new Error(`El modal con id '${modalId}' no se encontró.`);
    }

    // Cargar la instancia del modal de Bootstrap
    // @ts-ignore
    if(instancia){
      this.bootstrapModal = new bootstrap.Modal(this.modalElement, {
        backdrop: false
      });
    }
  }

  // Método para abrir el modal
  public open(): void {
    if (this.bootstrapModal) {
      this.manageBackdropRelativeToModal(true)
      this.bootstrapModal.show(); // Asegúrate de que 'show' se ejecute en el contexto correcto
      setTimeout(()=>{
        this.on('hidden.bs.modal', () => {
          console.log('cerrando modal')
          this.manageBackdropRelativeToModal(false)
        })
      }, 500)
      document.querySelectorAll("[data-modal-hidden]").forEach((item:Element) => {
        if(!item.classList.contains('d-none')){
          item.classList.add('d-none')
        }
      })
    } else {
      console.error('El modal de Bootstrap no está inicializado.');
    }
  }


  // Método para cerrar el modal
  public close(): void {
    if (this.bootstrapModal) {
      this.bootstrapModal.hide();
      this.manageBackdropRelativeToModal(false)
    } else {
      console.error('El modal de Bootstrap no está inicializado.');
    }
  }

  // Método para destruir el modal
  public dispose(): void {
    if (this.bootstrapModal) {
      this.bootstrapModal.dispose();
      this.manageBackdropRelativeToModal(false)
    } else {
      console.error('El modal de Bootstrap no está inicializado.');
    }
  }

  // Método para establecer contenido dinámico en el modal
  public setContent(content: string): void {
    if (this.modalElement) {
      const modalBody = this.modalElement.querySelector('.modal-body');
      if (modalBody) {
        modalBody.innerHTML = content;
      }
    }
  }

  // Método para agregar eventos al modal
  public on(event: string, callback: () => void): void {
    if (this.modalElement) {
      this.modalElement.addEventListener(event, callback);
    }
  }

  public convertToModal(options?: ModalOptions, open: boolean = true): void {
    if (!this.modalElement) {
      throw new Error("El elemento no está definido.");
    }

    // Agregar clases base solo si aún no las tiene
    if (!this.modalElement.classList.contains("modal")) {
      this.modalElement.classList.add("modal", "fade");
      this.modalElement.setAttribute("tabindex", "-1");
      this.modalElement.setAttribute("aria-hidden", "true");
    }

    // Revisar si el modal ya tiene la estructura requerida
    let modalDialog = this.modalElement.querySelector(".modal-dialog");
    if (!modalDialog) {
      modalDialog = document.createElement("div");
      modalDialog.classList.add("modal-dialog");

      // Aplicar opciones al modal-dialog
      if (options?.centered) {
        modalDialog.classList.add("modal-dialog-centered");
      }
      if (options?.scrollable) {
        modalDialog.classList.add("modal-dialog-scrollable");
      }
      if (options?.size) {
        modalDialog.classList.add(`modal-${options.size}`);
      }
      if(options?.fullscreenMdDown){
        modalDialog.classList.add("modal-fullscreen-md-down");
      }

      // Crear modal-content si no existe
      const modalContent = document.createElement("div");
      modalContent.classList.add("modal-content");
      modalContent.classList.add("z-index-999");

      // Mover el contenido actual dentro de modal-content
      while (this.modalElement.firstChild) {
        modalContent.appendChild(this.modalElement.firstChild);
      }

      modalDialog.appendChild(modalContent);
      this.modalElement.appendChild(modalDialog);
    }

    // Verificar si la instancia de Bootstrap ya existe, y si no, inicializarla
    if (!this.bootstrapModal) {
      // @ts-ignore
      this.bootstrapModal = new bootstrap.Modal(this.modalElement,{
        backdrop: false
      });
    }
    if(options?.modalHeader){
      this.addClass(options?.modalHeader, "modal-header")
      const headerElement = this.modalElement.querySelector('.modal-header');
      if (!headerElement.querySelector('.btn-close')) {
        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'btn-close';
        closeButton.setAttribute('data-bs-dismiss', 'modal');
        closeButton.setAttribute('aria-label', 'Close');

        // Agregar el botón al header
        headerElement.appendChild(closeButton);
      }

    }
    if(options?.modalBody){
      if(typeof options?.modalBody === 'string'){
        this.addClass(options?.modalBody, "modal-body")
      }else if(Array.isArray(options?.modalBody)){
        options?.modalBody.forEach(item =>{
          this.addClass(item, "modal-body")
        })
      }
    }

    // Abrir el modal si el parámetro "open" es verdadero
    if (open) {
      this.open();
    }
    if(options?.overflowElement){
      this.addClass(options?.overflowElement, "overflow-auto")
    }
    this.on('hidden.bs.modal', () => {
      this.revertFromModal();
    })
  }

  public revertFromModal(): void {
    console.log("revertFromModal");
    if (!this.modalElement) {
      throw new Error("El elemento no está definido.");
    }

    // Cerrar el modal si está abierto
    if (this.bootstrapModal) {
      this.bootstrapModal.hide();
      this.bootstrapModal = null; // Eliminar la instancia de Bootstrap Modal
    }

    // Eliminar clases de Bootstrap
    this.modalElement.classList.remove("modal", "fade");
    this.modalElement.removeAttribute("tabindex");
    this.modalElement.removeAttribute("aria-hidden");

    // Eliminar modal-dialog y su contenido, si existe
    const modalDialog = this.modalElement.querySelector(".modal-dialog");
    if (modalDialog) {
      // Mover el contenido de modal-content de regreso a modalElement
      const modalContent = modalDialog.querySelector(".modal-content");
      if (modalContent) {
        while (modalContent.firstChild) {
          this.modalElement.appendChild(modalContent.firstChild);
        }
      }

      // Remover modal-dialog completamente
      modalDialog.remove();
    }

    // Eliminar clases adicionales relacionadas con las opciones (como "modal-fullscreen-md-down", "modal-header", etc.)
    const classesToRemove = [
      "modal-dialog-centered",
      "modal-dialog-scrollable",
      "modal-fullscreen-md-down",
      "modal-header",
      "modal-body",
      "modal-footer",
      "z-index-999", // Clase agregada dinámicamente
    ];

    classesToRemove.forEach((className) => this.modalElement.classList.remove(className));

    // Remover botón de cerrar (.btn-close), si existe
    const closeButton = this.modalElement.querySelector(".btn-close");
    if (closeButton) {
      closeButton.remove();
    }
    this.modalElement.removeAttribute("style");
  }

  public manageBackdropRelativeToModal(create: boolean, modalElement?: HTMLElement): void {
    const parent = this.modalElement.parentElement; // Obtener el padre del modalElement

    if (!parent) {
      console.error('modalElement no tiene un elemento padre.');
      return;
    }

    // Buscar un backdrop existente dentro del mismo padre
    const existingBackdrop = parent.querySelector('.modal-backdrop');

    if (create) {
      // Crear el backdrop solo si no existe
      if (!existingBackdrop) {
        const backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop fade show';
        parent.insertBefore(backdrop, this.modalElement); // Insertarlo antes o en cualquier posición deseada
      }

    } else {
      // Eliminar el backdrop existente del mismo nivel del modalElement
      if (existingBackdrop) {
        document.querySelectorAll('.modal-backdrop').forEach(backdrop =>
          backdrop.remove()
        )

      }
      document.querySelectorAll("[data-modal-hidden]").forEach((item:Element) => {
        if(item.classList.contains('d-none')){
          item.classList.remove('d-none')
        }
      })
    }
  }
  private addClass(element: string, className: string): void {
    let header = this.modalElement.querySelector(element)
    if(header){
      if(!header.classList.contains(className)){
        header.classList.add(className);
      }
    }
  }
}
