(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    initDropdowns();
    initFlashMessages();
    initDeleteConfirmations();
    initTabSwitching();
    initCartQuantityUpdates();
    initMobileMenu();
    initSearchClear();
    initRatingStars();
  });

  function initDropdowns() {
    var toggles = document.querySelectorAll("[data-dropdown-toggle]");
    toggles.forEach(function (toggle) {
      var targetId = toggle.getAttribute("data-dropdown-toggle");
      var target = document.getElementById(targetId);
      if (!target) return;

      toggle.addEventListener("click", function (e) {
        e.stopPropagation();
        var isHidden = target.classList.contains("hidden");
        closeAllDropdowns();
        if (isHidden) {
          target.classList.remove("hidden");
          toggle.setAttribute("aria-expanded", "true");
        }
      });
    });

    document.addEventListener("click", function (e) {
      var openDropdowns = document.querySelectorAll("[data-dropdown-toggle]");
      openDropdowns.forEach(function (toggle) {
        var targetId = toggle.getAttribute("data-dropdown-toggle");
        var target = document.getElementById(targetId);
        if (!target) return;
        if (!target.contains(e.target) && !toggle.contains(e.target)) {
          target.classList.add("hidden");
          toggle.setAttribute("aria-expanded", "false");
        }
      });
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        closeAllDropdowns();
      }
    });
  }

  function closeAllDropdowns() {
    var toggles = document.querySelectorAll("[data-dropdown-toggle]");
    toggles.forEach(function (toggle) {
      var targetId = toggle.getAttribute("data-dropdown-toggle");
      var target = document.getElementById(targetId);
      if (target) {
        target.classList.add("hidden");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  function initFlashMessages() {
    var flashMessages = document.querySelectorAll("[data-flash-message]");
    flashMessages.forEach(function (msg) {
      var duration = parseInt(msg.getAttribute("data-flash-duration") || "5000", 10);

      setTimeout(function () {
        dismissFlashMessage(msg);
      }, duration);

      var closeBtn = msg.querySelector("[data-flash-close]");
      if (closeBtn) {
        closeBtn.addEventListener("click", function () {
          dismissFlashMessage(msg);
        });
      }
    });
  }

  function dismissFlashMessage(el) {
    el.style.transition = "opacity 0.3s ease, transform 0.3s ease";
    el.style.opacity = "0";
    el.style.transform = "translateY(-10px)";
    setTimeout(function () {
      if (el.parentNode) {
        el.parentNode.removeChild(el);
      }
    }, 300);
  }

  function initDeleteConfirmations() {
    var deleteButtons = document.querySelectorAll("[data-confirm-delete]");
    deleteButtons.forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        var message = btn.getAttribute("data-confirm-delete") || "Are you sure you want to delete this item?";
        if (!confirm(message)) {
          e.preventDefault();
          e.stopPropagation();
        }
      });
    });

    var deleteForms = document.querySelectorAll("form[data-confirm-submit]");
    deleteForms.forEach(function (form) {
      form.addEventListener("submit", function (e) {
        var message = form.getAttribute("data-confirm-submit") || "Are you sure you want to proceed?";
        if (!confirm(message)) {
          e.preventDefault();
          e.stopPropagation();
        }
      });
    });
  }

  function initTabSwitching() {
    var tabContainers = document.querySelectorAll("[data-tabs]");
    tabContainers.forEach(function (container) {
      var tabButtons = container.querySelectorAll("[data-tab-target]");
      tabButtons.forEach(function (btn) {
        btn.addEventListener("click", function () {
          var targetId = btn.getAttribute("data-tab-target");
          var tabGroup = container.getAttribute("data-tabs");

          var allButtons = container.querySelectorAll("[data-tab-target]");
          allButtons.forEach(function (b) {
            b.classList.remove("border-indigo-500", "text-indigo-600", "bg-indigo-50");
            b.classList.add("border-transparent", "text-gray-500");
            b.setAttribute("aria-selected", "false");
          });

          btn.classList.add("border-indigo-500", "text-indigo-600", "bg-indigo-50");
          btn.classList.remove("border-transparent", "text-gray-500");
          btn.setAttribute("aria-selected", "true");

          var allPanels = document.querySelectorAll("[data-tab-panel" + (tabGroup ? '="' + tabGroup + '"' : "") + "]");
          allPanels.forEach(function (panel) {
            panel.classList.add("hidden");
          });

          var targetPanel = document.getElementById(targetId);
          if (targetPanel) {
            targetPanel.classList.remove("hidden");
          }
        });
      });
    });
  }

  function initCartQuantityUpdates() {
    var quantityForms = document.querySelectorAll("[data-cart-quantity-form]");
    quantityForms.forEach(function (form) {
      var decrementBtn = form.querySelector("[data-quantity-decrement]");
      var incrementBtn = form.querySelector("[data-quantity-increment]");
      var quantityInput = form.querySelector("[data-quantity-input]");

      if (!quantityInput) return;

      var minVal = parseInt(quantityInput.getAttribute("min") || "1", 10);
      var maxVal = parseInt(quantityInput.getAttribute("max") || "999", 10);

      if (decrementBtn) {
        decrementBtn.addEventListener("click", function (e) {
          e.preventDefault();
          var current = parseInt(quantityInput.value, 10) || minVal;
          if (current > minVal) {
            quantityInput.value = current - 1;
            submitCartForm(form);
          }
        });
      }

      if (incrementBtn) {
        incrementBtn.addEventListener("click", function (e) {
          e.preventDefault();
          var current = parseInt(quantityInput.value, 10) || minVal;
          if (current < maxVal) {
            quantityInput.value = current + 1;
            submitCartForm(form);
          }
        });
      }

      quantityInput.addEventListener("change", function () {
        var val = parseInt(quantityInput.value, 10);
        if (isNaN(val) || val < minVal) {
          quantityInput.value = minVal;
        } else if (val > maxVal) {
          quantityInput.value = maxVal;
        }
        submitCartForm(form);
      });
    });
  }

  function submitCartForm(form) {
    var autoSubmit = form.getAttribute("data-auto-submit");
    if (autoSubmit === "false") return;
    form.submit();
  }

  function initMobileMenu() {
    var menuToggle = document.querySelector("[data-mobile-menu-toggle]");
    var menuTarget = document.querySelector("[data-mobile-menu]");

    if (!menuToggle || !menuTarget) return;

    menuToggle.addEventListener("click", function () {
      var isHidden = menuTarget.classList.contains("hidden");
      if (isHidden) {
        menuTarget.classList.remove("hidden");
        menuToggle.setAttribute("aria-expanded", "true");
      } else {
        menuTarget.classList.add("hidden");
        menuToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  function initSearchClear() {
    var clearButtons = document.querySelectorAll("[data-search-clear]");
    clearButtons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var formId = btn.getAttribute("data-search-clear");
        var form = formId ? document.getElementById(formId) : btn.closest("form");
        if (!form) return;

        var inputs = form.querySelectorAll("input[type='text'], input[type='search'], select");
        inputs.forEach(function (input) {
          if (input.tagName === "SELECT") {
            input.selectedIndex = 0;
          } else {
            input.value = "";
          }
        });

        form.submit();
      });
    });
  }

  function initRatingStars() {
    var ratingContainers = document.querySelectorAll("[data-rating-input]");
    ratingContainers.forEach(function (container) {
      var hiddenInput = container.querySelector("input[type='hidden']");
      var stars = container.querySelectorAll("[data-star-value]");

      if (!hiddenInput || stars.length === 0) return;

      stars.forEach(function (star) {
        star.addEventListener("mouseenter", function () {
          var val = parseInt(star.getAttribute("data-star-value"), 10);
          highlightStars(stars, val);
        });

        star.addEventListener("mouseleave", function () {
          var currentVal = parseInt(hiddenInput.value, 10) || 0;
          highlightStars(stars, currentVal);
        });

        star.addEventListener("click", function () {
          var val = parseInt(star.getAttribute("data-star-value"), 10);
          hiddenInput.value = val;
          highlightStars(stars, val);
        });
      });

      var initialVal = parseInt(hiddenInput.value, 10) || 0;
      if (initialVal > 0) {
        highlightStars(stars, initialVal);
      }
    });
  }

  function highlightStars(stars, rating) {
    stars.forEach(function (star) {
      var val = parseInt(star.getAttribute("data-star-value"), 10);
      if (val <= rating) {
        star.classList.add("text-yellow-400");
        star.classList.remove("text-gray-300");
      } else {
        star.classList.remove("text-yellow-400");
        star.classList.add("text-gray-300");
      }
    });
  }
})();