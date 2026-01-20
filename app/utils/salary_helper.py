class SalaryCalculator:
    LUONG_CO_SO = 2_340_000
    GIAM_TRU_BAN_THAN = 11_000_000
    GIAM_TRU_PHU_THUOC = 4_400_000

    LUONG_TOI_THIEU_VUNG = {1: 4_960_000, 2: 4_410_000, 3: 3_860_000, 4: 3_250_000}

    RATE_BHXH = 0.08
    RATE_BHYT = 0.015
    RATE_BHTN = 0.01

    @staticmethod
    def calculate_tax(taxable_income):
        """Tính thuế TNCN dựa trên thu nhập tính thuế"""
        if taxable_income <= 0:
            return 0

        brackets = [
            (5_000_000, 0.05, 0),
            (10_000_000, 0.10, 250_000),
            (18_000_000, 0.15, 750_000),
            (32_000_000, 0.20, 1_650_000),
            (52_000_000, 0.25, 3_250_000),
            (80_000_000, 0.30, 5_850_000),
            (float("inf"), 0.35, 9_850_000),
        ]

        tax = 0
        for limit, rate, subtraction in brackets:
            if taxable_income <= limit:
                tax = taxable_income * rate - subtraction
                break
            if limit == float("inf"):  # Bậc cuối cùng
                tax = taxable_income * rate - subtraction

        return max(0, tax)

    @classmethod
    def gross_to_net(
        cls, gross_salary, region_id=1, num_dependents=0, insurance_salary=None
    ):
        """
        Tính Net từ Gross.
        insurance_salary: Mức lương đóng bảo hiểm (nếu None thì lấy Gross, nhưng check trần)
        """
        cap_bhxh_bhyt = 20 * cls.LUONG_CO_SO
        cap_bhtn = 20 * cls.LUONG_TOI_THIEU_VUNG.get(int(region_id), 4_960_000)

        if insurance_salary is None or insurance_salary == "full":
            base_bhxh = min(gross_salary, cap_bhxh_bhyt)
            base_bhtn = min(gross_salary, cap_bhtn)
        else:
            base_bhxh = min(gross_salary, cap_bhxh_bhyt)
            base_bhtn = min(gross_salary, cap_bhtn)

        bhxh = base_bhxh * cls.RATE_BHXH
        bhyt = base_bhxh * cls.RATE_BHYT
        bhtn = base_bhtn * cls.RATE_BHTN
        total_insurance = bhxh + bhyt + bhtn

        income_before_tax = gross_salary - total_insurance

        total_deduction = cls.GIAM_TRU_BAN_THAN + (
            num_dependents * cls.GIAM_TRU_PHU_THUOC
        )
        taxable_income = income_before_tax - total_deduction

        tax = cls.calculate_tax(taxable_income)

        net_salary = gross_salary - total_insurance - tax

        return {
            "gross": gross_salary,
            "net": net_salary,
            "bhxh": bhxh,
            "bhyt": bhyt,
            "bhtn": bhtn,
            "total_insurance": total_insurance,
            "income_before_tax": income_before_tax,
            "taxable_income": max(0, taxable_income),
            "tax": tax,
            "dependents_deduction": num_dependents * cls.GIAM_TRU_PHU_THUOC,
        }

    @classmethod
    def net_to_gross(cls, target_net, region_id=1, num_dependents=0):
        """
        Tính Gross từ Net.
        Sử dụng phương pháp lặp (Binary Search) để tìm Gross chính xác.
        """
        lower = target_net
        upper = (
            target_net * 2
        )  # Giả định Gross không quá 2 lần Net (trừ khi lương siêu cao)

        while True:
            res = cls.gross_to_net(upper, region_id, num_dependents)
            if res["net"] >= target_net:
                break
            upper *= 1.5
            lower = upper / 2

        for _ in range(100):  # Tối đa 100 lần lặp
            mid = (lower + upper) / 2
            res = cls.gross_to_net(mid, region_id, num_dependents)

            if abs(res["net"] - target_net) < 1:  # Chấp nhận sai số 1 đồng
                return res

            if res["net"] < target_net:
                lower = mid
            else:
                upper = mid

        return cls.gross_to_net(upper, region_id, num_dependents)
