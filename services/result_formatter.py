class ResultFormatter:
    COLUMN_WIDTH = 24

    @staticmethod
    def format_table(headers, rows):
        # Simple table formatter
        if not rows:
            return "No data to display."

        width = ResultFormatter.COLUMN_WIDTH
        column_count = len(headers)

        separator = "+" + "+".join("-" * (width + 2) for _ in headers) + "+"

        header_row = ResultFormatter._format_row(headers, column_count, width)

        data_rows = []
        for row in rows:
            data_rows.append(ResultFormatter._format_row(row, column_count, width))

        table = [separator, header_row, separator] + data_rows + [separator]
        return "\n".join(table)

    @staticmethod
    def _format_row(row, column_count, width):
        cells = []
        for i in range(column_count):
            value = str(row[i]) if i < len(row) else ""
            cells.append(value[:width].ljust(width))
        return "|" + "|".join(f" {cell} " for cell in cells) + "|"
