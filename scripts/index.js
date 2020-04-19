(function() {
    var donation = {
        type: window.default_type,
        amount: window.default_amount * 100, // cents
        project: null,
        comment: null
    };

    function formatCents(cents) {
        var dollars = Math.floor(cents/100);
        var leftover = Math.floor(cents%100);
        return String(dollars)+"."+String(leftover+100).substring(1);
    }

    function updateFee() {
        var amt = donation.amount;
        amt -= 30;
        amt *= 0.971;
        amt = Math.floor(amt);
        var fee = donation.amount-amt;
        var pct = ((fee/donation.amount)*100).toFixed(1);
        document.getElementById("after-fees").textContent = formatCents(amt);
        document.getElementById("fee").textContent = formatCents(fee);
        document.getElementById("fee-pct").textContent = pct;
        document.getElementById("fee-pct-wrapper").style.fontWeight = pct > 10 ? 700 : 400;
    }

    function selectAmount(e) {
        e.preventDefault();
        document.querySelector(".amounts .active").classList.remove("active");
        e.target.classList.add("active");
        var custom = document.querySelector("#custom-amount");
        var amount = e.target.dataset.amount;
        if (amount === "custom") {
            custom.classList.remove("hidden");
            donation.amount = +document.querySelector("#custom-amount-text").value * 100;
        } else {
            custom.classList.add("hidden");
            donation.amount = +e.target.dataset.amount * 100;
        }
        updateFee();
    }

    function selectFrequency(e) {
        e.preventDefault();
        document.querySelector(".frequencies .active").classList.remove("active");
        e.target.classList.add("active");
        donation.type = e.target.dataset.frequency;
    }

    var amounts = document.querySelectorAll(".amounts button");
    for (var i = 0; i < amounts.length; i++) {
        amounts[i].addEventListener("click", selectAmount);
    }

    var frequencies = document.querySelectorAll(".frequencies button");
    for (var i = 0; i < frequencies.length; i++) {
        frequencies[i].addEventListener("click", selectFrequency);
    }

    document.getElementById("custom-amount-text").addEventListener("change", function(e) {
        var value = +e.target.value;
        if (isNaN(value) || value <= 1) {
            value = 1;
        }
        e.target.value = value.toFixed(2);
        donation.amount = value * 100;
        updateFee();
    });

    var project = document.getElementById("project")
    if (project) {
        project.addEventListener("change", function(e) {
            if (e.target.value === "null") {
                donation.project = null;
            } else {
                donation.project = e.target.value;
            }
        });
    }

    document.getElementById("donate-button").addEventListener("click", function(e) {
        e.preventDefault();
        if (e.target.getAttribute("disabled")) {
            return;
        }

        donation.comment = document.getElementById("comments").value;

        var handler = StripeCheckout.configure({
            name: your_name,
            email: window.email,
            key: window.stripe_key,
            image: window.avatar,
            locale: 'auto',
            description: donation.type == "monthly" ? i18n["Monthly Donation"] : i18n["One-time Donation"],
            panelLabel: i18n["Donate "] + "{{amount}}",
            amount: donation.amount,
            currency: currency,
            token: function(token) {
                e.target.setAttribute("disabled", "");
                e.target.textContent = i18n["Submitting..."];

                var data = new FormData();
                data.append("stripe_token", token.id);
                data.append("email", token.email);
                data.append("amount", donation.amount);
                data.append("type", donation.type);
                if (donation.comment !== null) {
                    data.append("comment", donation.comment);
                }
                if (donation.project !== null) {
                    data.append("project", donation.project);
                }
                var xhr = new XMLHttpRequest();
                xhr.open("POST", "donate");
                xhr.onload = function() {
                    var res = JSON.parse(this.responseText);
                    if (res.success) {
                        document.getElementById("donation-stuff").classList.add("hidden");
                        document.getElementById("thanks").classList.remove("hidden");
                        if (res.new_account) {
                            document.getElementById("new-donor-password").classList.remove("hidden");
                            document.getElementById("reset-token").value = res.password_reset;
                        }
                    } else {
                        var errors = document.getElementById("errors");
                        errors.classList.remove("hidden");
                        errors.querySelector("p").textContent = res.reason;
                        e.target.removeAttribute("disabled");
                        e.target.textContent = i18n["Donate"];
                    }
                };
                xhr.send(data);
            }
        });

        handler.open();
    });

    document.addEventListener("DOMContentLoaded", function() {
        updateFee();
    });
})();
