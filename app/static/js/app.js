const translations = {
  en: {
    title: "Download Video or Convert to MP3",
    urlLabel: "Enter Video URL:",
    placeholder: "Enter video URL",
    formatLabel: "Select download format:",
    mp3: "Download as MP3",
    mp4: "Download as MP4",
    download: "Download",
    reset: "Reset",
    dark: "🌙",
    light: "☀️",
    langToggle: "AR",
    success: "✅ Your download completed successfully!",
    invalidUrl: "Please enter a valid URL.",
    unexpected: "An unexpected error occurred.",
    qrMessage: "Share this with a friend!",
    loading: "Loading...",
    converting: "Converting MP3...",
    downloading: "Downloading MP4...",
  },
  ar: {
    title: "تحميل الفيديو أو تحويله إلى MP3",
    urlLabel: "أدخل رابط الفيديو:",
    placeholder: "أدخل رابط الفيديو",
    formatLabel: "اختر صيغة التحميل:",
    mp3: "تحميل MP3",
    mp4: "تحميل MP4",
    download: "تحميل",
    reset: "إعادة تعيين",
    dark: "🌙 ",
    light: "☀️",
    langToggle: "EN",
    success: "✅ بدأ التحميل!",
    invalidUrl: "يرجى إدخال رابط صحيح.",
    unexpected: "حدث خطأ غير متوقع.",
    qrMessage: "شارك هذا الرابط مع صديق!",
    loading: "جارٍ التحميل...",
    converting: "جارٍ التحويل إلى MP3 متوافق مع الواتساب...",
    downloading: "جارٍ تنزيل MP4 متوافق مع الواتساب...",
  },
};

function getLang() {
  return localStorage.getItem("lang") || "en";
}

function getTheme() {
  return (
    localStorage.getItem("theme") ||
    (window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light")
  );
}

function isMobile() {
  return /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
}

function showToast(msg) {
  $("#toast").text(msg).fadeIn(200).delay(2500).fadeOut(300);
}

function setLoadingText(type = "loading") {
  const t = translations[getLang()];
  const text = t[type] || t.loading;
  $("#loadingText").text(text);
}

function toggleOverlay(show, type = "loading") {
  setLoadingText(type);
  $("#loadingOverlay").css("display", show ? "flex" : "none");
}

function setMode(mode) {
  document.body.classList.toggle("dark-mode", mode === "dark");
  localStorage.setItem("theme", mode);
  updateText();
}

function getQrMessage() {
  const lang = getLang();
  if (isMobile()) {
    return translations[lang]?.qrMessage || "Share this with a friend!";
  }
  return lang === "ar"
    ? "نزّل هذا على هاتفك المحمول"
    : "Download this on mobile";
}

function updateText() {
  const lang = getLang();
  const t = translations[lang];
  $("#title").text(t.title);
  $("#urlLabel").text(t.urlLabel);
  $("#url").attr("placeholder", t.placeholder);
  $("#optionLabel").text(t.formatLabel);
  $("#mp3Option").text(t.mp3);
  $("#mp4Option").text(t.mp4);
  $("#downloadButton").text(t.download);
  $("#resetButton").text(t.reset);
  $("#modeToggle").text(
    document.body.classList.contains("dark-mode") ? t.light : t.dark
  );
  $("#langToggle").text(t.langToggle);
  $("html").attr("dir", lang === "ar" ? "rtl" : "ltr");
  $("#qrMessage").text(getQrMessage());
}

function setLanguage(lang) {
  localStorage.setItem("lang", lang);
  updateText();
}

function generateQRCode(downloadUrl) {
  if (isMobile()) return;

  $("#qrContainer").show();
  const canvas = document.getElementById("qrCanvas");
  if (canvas) {
    // Generate absolute URL for QR code
    const absoluteUrl = window.location.origin + downloadUrl;
    new QRious({
      element: canvas,
      value: absoluteUrl,
      size: 150,
    });
  }
}

function handleDownloadSuccess(response, t) {
  const filename = response.filename;
  const downloadUrl = `/download_file?file=${encodeURIComponent(filename)}`;

  // Show success message
  showToast(`${t.success} (${filename})`);

  // Handle download based on device type
  if (isMobile()) {
    // For mobile, use direct navigation which works more reliably
    setTimeout(() => {
      window.location.href = downloadUrl;
    }, 500);
  } else {
    // For desktop, use programmatic download
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = filename;
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // Clear the URL input
  $("#url").val("");

  // Generate QR code for easy sharing
  generateQRCode(downloadUrl);
}

$(document).ready(function () {
  setMode(getTheme());
  setLanguage(getLang());

  $("#modeToggle").click(() =>
    setMode(document.body.classList.contains("dark-mode") ? "light" : "dark")
  );
  $("#langToggle").click(() => setLanguage(getLang() === "en" ? "ar" : "en"));

  $("#downloadForm").submit(function (event) {
    event.preventDefault();
    $("#message").empty();

    const url = $("#url").val().trim();
    const option = $("#option").val();
    const t = translations[getLang()];

    if (!url) {
      showToast(t.invalidUrl);
      return;
    }

    toggleOverlay(
      true,
      option === "mp3"
        ? "converting"
        : option === "mp4"
        ? "downloading"
        : "loading"
    );

    $.ajax({
      type: "POST",
      url: "/download",
      data: { url, option },
      success: function (response) {
        toggleOverlay(false);
        if (response.status === "success") {
          handleDownloadSuccess(response, t);
        } else {
          showToast(`Error: ${response.message}`);
        }
      },
      error: function (xhr, status, error) {
        toggleOverlay(false);
        if (xhr.responseJSON && xhr.responseJSON.message) {
          showToast(`Error: ${xhr.responseJSON.message}`);
        } else {
          showToast(t.unexpected);
        }
      },
    });
  });

  $("#resetButton, #url, #option").on("click input change", function () {
    $("#message").empty();
    $("#qrContainer").hide();
  });
});
