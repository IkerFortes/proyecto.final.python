  document.addEventListener("DOMContentLoaded", function() {
    // Obtiene la URL actual (ejemplo: index.html)
    const currentPath = window.location.pathname.split("/").pop();

    // console.log(currentPath)

    // Selecciona todos los enlaces de la navegación
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
      // Si el href del enlace coincide con la página actual
      if (link.getAttribute('href') === currentPath) {
        // Agrega la clase 'active' al elemento padre (el <li>)
        link.parentElement.classList.add('active');
      } else {
        // Remueve la clase de los que no coinciden
        link.parentElement.classList.remove('active');
      }
    });
  });