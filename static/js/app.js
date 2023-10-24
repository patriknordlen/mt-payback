$(document).ready(() => {
  if (localStorage.getItem("ticketholders")) {
    let ticketholders = JSON.parse(localStorage.getItem("ticketholders"));
    loadTicketHolders(ticketholders);
    loadTicketData(ticketholders[localStorage.getItem("ticketholder")]);
  }

  $("#expirydate").val(localStorage.getItem("expirydate"));
  $("#ticket").val(localStorage.getItem("ticket"));

  loadDepartures();
});

$("#closemodal").click(() => {
  $("#ticketholderdialog").removeAttr("open");
});

$("#newticketholder").click(() => {
  $("#holderdialogmode").val("save");
  $("#ticketholdertitle").text("Add ticket holder");
  $("#firstname").val("");
  $("#surname").val("");
  $("#streetaddress").val("");
  $("#postalcode").val("");
  $("#city").val("");
  $("#ssn").val("");
  $("#telno").val("");
  $("#email").val("");
  $("#submitholder").text("Add");

  $("#ticketholderdialog").attr("open", "true");
});

$("#editticketholder").click(() => {
  let ticketholders = JSON.parse(localStorage.getItem("ticketholders"));
  let ticketholder = ticketholders[$("#ticketholder").val()];

  $("#holderdialogmode").val("edit");
  $("#ticketholdertitle").text("Edit ticket holder");
  $("#firstname").val(ticketholder.firstName);
  $("#surname").val(ticketholder.surName);
  $("#streetaddress").val(ticketholder.streetNameAndNumber);
  $("#postalcode").val(ticketholder.postalCode);
  $("#city").val(ticketholder.city);
  $("#ssn").val(ticketholder.identityNumber);
  $("#telno").val(ticketholder.mobileNumber);
  $("#email").val(ticketholder.email);
  $("#submitholder").text("Save");

  $("#ticketholderdialog").attr("open", "true");
});

$("#saveticket").click(function (e) {
  localStorage.setItem("ticketholder", $("#ticketholder").val());
  localStorage.setItem("ticket", $("#ticket").val());
  localStorage.setItem("expirydate", $("#expirydate").val());

  $("#ticketforminfo").attr("style", "color:green").text("Details saved"),
    e.preventDefault();
});

$("#ticketholderform").submit(function (e) {
  let ticketholders = {};

  if (localStorage.getItem("ticketholders")) {
    ticketholders = JSON.parse(localStorage.getItem("ticketholders"));
  }

  ticketholders[$("#firstname").val()] = {
    firstName: $("#firstname").val(),
    surName: $("#surname").val(),
    city: $("#city").val(),
    streetNameAndNumber: $("#streetaddress").val(),
    postalCode: $("#postalcode").val(),
    identityNumber: $("#ssn").val(),
    mobileNumber: $("#telno").val(),
    email: $("#email").val(),
  };

  localStorage.setItem("ticketholders", JSON.stringify(ticketholders));
  loadTicketHolders(ticketholders);
  $("#ticketholderdialog").removeAttr("open");

  e.preventDefault();
});

$("#paybackform").submit(function (e) {
  if (
    localStorage.getItem("expirydate") >
      new Date().toLocaleDateString("sv-SE") ||
    confirm(
      `The ticket expired on ${localStorage.getItem(
        "expirydate"
      )}! Do you want to submit anyway?`
    )
  ) {
    jsonData = {};
    const data = $(this).serializeArray();
    jQuery.each(data, function () {
      jsonData[this.name] = this.value || "";
    });

    jsonData["customer"] = JSON.parse(localStorage.getItem("ticketholders"))[
      localStorage.getItem("ticketholder")
    ];
    $.post({
      url: "/api/submit",
      contentType: "application/json",
      data: JSON.stringify(jsonData),
      beforeSend: () =>
        $("#result")
          .attr("style", "color:green")
          .attr("aria-busy", "true")
          .text(""),
      success: (data) => $("#result").attr("aria-busy", "false").text(data),
      error: () =>
        $("#result")
          .attr("aria-busy", "false")
          .attr("style", "color:red")
          .text("Request failed"),
    });
  }
  e.preventDefault();
});

$("#departureLocation").on("change", async (event) => {
  const departureStation = event.target.value;

  await $.get({
    url: `/api/arrival_stations/${departureStation}`,
    success: (response) => {
      $("#arrivalLocation").empty();
      $.each(response.stations, (i, val) => {
        $("#arrivalLocation").append(
          $("<option>", {
            value: val.name,
            text: val.longname,
          })
        );
      });
    },
  });

  await loadDepartures();
});

$("#departureDate").on("change", loadDepartures);

$("#arrivalLocation").on("change", loadDepartures);

function loadTicketData(th) {
  let expiryDate = localStorage.getItem("expirydate");

  if (expiryDate < new Date().toLocaleDateString("sv-SE")) {
    $("#ticketsummary").attr("style", "color:red");
    $("#ticketsummary").text(
      `Ticket (${th.firstName} ${th.surName}'s ticket - EXPIRED ${expiryDate})`
    );
  } else {
    $("#ticketsummary").text(
      `Ticket (${th.firstName} ${th.surName}'s ticket expiring ${expiryDate})`
    );
  }
}

function loadTicketHolders(thObj) {
  $("#ticketholder").html("");

  $.each(Object.keys(thObj), (i, key) => {
    $("#ticketholder").append(
      $("<option>", {
        value: thObj[key].firstName,
        text: `${thObj[key].firstName} ${thObj[key].surName}`,
      })
    );
  });
}

function loadDepartures() {
  $.get({
    url: `/api/departures/${$("#departureLocation").val()}/${$(
      "#arrivalLocation"
    ).val()}/${$("#departureDate").val()}`,
    dataType: "json",
    success: (response) => {
      $("#departures").empty();
      $.each(response, (i, val) => {
        $("#departures").append(
          $("<option>", {
            value: getFakeISOString(new Date(val)),
            text: val.split("T")[1],
          })
        );
      });
      $("#departures").val($("#departures option:last").val());
    },
    error: (e) => console.log(e),
  });
}

// Workaround for Mälartåg's horrible (non-)use of timezones - even though
// the API is expecting ISO8601 formatted dates, times are expected to be local
// rather than in Z timezone.
function getFakeISOString(date) {
  let d = new Date(date),
    month = "" + (d.getMonth() + 1),
    day = "" + d.getDate(),
    year = "" + d.getFullYear(),
    hours = "" + d.getHours(),
    minutes = "" + d.getMinutes(),
    seconds = "" + d.getSeconds();
  month = month.length < 2 ? "0" + month : month;
  day = day.length < 2 ? "0" + day : day;
  hours = hours.length < 2 ? "0" + hours : hours;
  minutes = minutes.length < 2 ? "0" + minutes : minutes;
  seconds = seconds.length < 2 ? "0" + seconds : seconds;
  return (
    [year, month, day].join("-") +
    "T" +
    [hours, minutes, seconds].join(":") +
    ".000Z"
  );
}
