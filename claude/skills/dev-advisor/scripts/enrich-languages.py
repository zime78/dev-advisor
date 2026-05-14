#!/usr/bin/env python3
"""dev-advisor 언어 reference에 공식 문서 링크와 실사용 예제를 보강한다."""

from __future__ import annotations

import re
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
LANG_DIR = SKILL_DIR / "references" / "languages"


DOCS = {
    "abap": [
        ("SAP ABAP Keyword Documentation", "https://help.sap.com/doc/abapdocu_latest_index_htm/latest/en-US/index.htm"),
        ("ABAP Platform", "https://help.sap.com/docs/abap-platform"),
        ("ABAP Development Tools", "https://tools.hana.ondemand.com/#abap"),
    ],
    "ada": [
        ("Ada Reference Manual", "https://www.adaic.org/resources/add_content/standards/12rm/html/RM-TTL.html"),
        ("Ada Resource Association", "https://www.adaic.org/"),
        ("GNAT User's Guide", "https://gcc.gnu.org/onlinedocs/gnat_ugn/"),
    ],
    "apex": [
        ("Apex Developer Guide", "https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/"),
        ("Apex Reference Guide", "https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/"),
        ("Salesforce CLI", "https://developer.salesforce.com/tools/salesforcecli"),
    ],
    "assembly": [
        ("Intel Architecture Software Developer Manuals", "https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html"),
        ("GNU Assembler Manual", "https://sourceware.org/binutils/docs/as/"),
        ("NASM Documentation", "https://www.nasm.us/docs.php"),
    ],
    "autohotkey": [
        ("AutoHotkey Documentation", "https://www.autohotkey.com/docs/v2/"),
        ("AutoHotkey Language Reference", "https://www.autohotkey.com/docs/v2/Language.htm"),
        ("AutoHotkey Script Library", "https://www.autohotkey.com/docs/v2/lib/"),
    ],
    "awk": [
        ("GNU awk User's Guide", "https://www.gnu.org/software/gawk/manual/gawk.html"),
        ("The AWK Programming Language", "https://pubs.opengroup.org/onlinepubs/9699919799/utilities/awk.html"),
        ("GNU awk Download", "https://www.gnu.org/software/gawk/"),
    ],
    "bash-shell": [
        ("GNU Bash Manual", "https://www.gnu.org/software/bash/manual/bash.html"),
        ("Bash Reference Manual", "https://www.gnu.org/software/bash/manual/"),
        ("Shell Command Language", "https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html"),
    ],
    "c": [
        ("ISO C Working Group", "https://www.open-std.org/jtc1/sc22/wg14/"),
        ("C Reference", "https://en.cppreference.com/w/c"),
        ("GCC C Language Extensions", "https://gcc.gnu.org/onlinedocs/gcc/C-Extensions.html"),
    ],
    "carbon": [
        ("Carbon Language", "https://carbon-lang.dev/"),
        ("Carbon GitHub", "https://github.com/carbon-language/carbon-lang"),
        ("Carbon Toolchain", "https://github.com/carbon-language/carbon-lang/tree/trunk/toolchain"),
    ],
    "clojure": [
        ("Clojure Reference", "https://clojure.org/reference/documentation"),
        ("Clojure API", "https://clojure.github.io/clojure/"),
        ("tools.build Guide", "https://clojure.org/guides/tools_build"),
    ],
    "cobol": [
        ("ISO COBOL Working Group", "https://www.open-std.org/jtc1/sc22/wg4/"),
        ("GnuCOBOL Programmer's Guide", "https://gnucobol.sourceforge.io/doc/gnucobol.html"),
        ("GnuCOBOL Project", "https://gnucobol.sourceforge.io/"),
    ],
    "cplusplus": [
        ("ISO C++", "https://isocpp.org/"),
        ("C++ Reference", "https://en.cppreference.com/w/cpp"),
        ("CMake Documentation", "https://cmake.org/documentation/"),
    ],
    "crystal": [
        ("Crystal Language Reference", "https://crystal-lang.org/reference/"),
        ("Crystal API", "https://crystal-lang.org/api/"),
        ("Shards Package Manager", "https://crystal-lang.org/reference/man/shards/"),
    ],
    "csharp": [
        ("C# Documentation", "https://learn.microsoft.com/dotnet/csharp/"),
        ("C# Language Reference", "https://learn.microsoft.com/dotnet/csharp/language-reference/"),
        (".NET CLI", "https://learn.microsoft.com/dotnet/core/tools/"),
    ],
    "cuda-c-cplusplus": [
        ("CUDA C++ Programming Guide", "https://docs.nvidia.com/cuda/cuda-c-programming-guide/"),
        ("CUDA Runtime API", "https://docs.nvidia.com/cuda/cuda-runtime-api/"),
        ("CUDA Toolkit Documentation", "https://docs.nvidia.com/cuda/"),
    ],
    "d": [
        ("D Language Specification", "https://dlang.org/spec/spec.html"),
        ("D Standard Library", "https://dlang.org/phobos/"),
        ("DUB Package Manager", "https://dub.pm/"),
    ],
    "dart": [
        ("Dart Documentation", "https://dart.dev/guides"),
        ("Dart Language", "https://dart.dev/language"),
        ("pub.dev Packages", "https://pub.dev/"),
    ],
    "delphi-object-pascal": [
        ("Delphi Documentation", "https://docwiki.embarcadero.com/RADStudio/en/Delphi_Language_Guide_Index"),
        ("Object Pascal Language Guide", "https://docwiki.embarcadero.com/RADStudio/en/Object_Pascal_Language_Guide"),
        ("RAD Studio Tools", "https://docwiki.embarcadero.com/RADStudio/en/Main_Page"),
    ],
    "elixir": [
        ("Elixir Documentation", "https://hexdocs.pm/elixir/"),
        ("Elixir Getting Started", "https://elixir-lang.org/getting-started/introduction.html"),
        ("Hex Package Manager", "https://hex.pm/"),
    ],
    "erlang": [
        ("Erlang Documentation", "https://www.erlang.org/docs"),
        ("Erlang Reference Manual", "https://www.erlang.org/doc/system/reference_manual.html"),
        ("rebar3", "https://www.rebar3.org/docs/"),
    ],
    "forth": [
        ("Forth 2012 Standard", "https://forth-standard.org/standard/"),
        ("Gforth Manual", "https://gforth.org/manual/"),
        ("Gforth Project", "https://gforth.org/"),
    ],
    "fortran": [
        ("Fortran Standards", "https://wg5-fortran.org/"),
        ("Fortran Package Manager", "https://fpm.fortran-lang.org/"),
        ("Fortran-lang Documentation", "https://fortran-lang.org/learn/"),
    ],
    "fsharp": [
        ("F# Documentation", "https://learn.microsoft.com/dotnet/fsharp/"),
        ("F# Language Reference", "https://learn.microsoft.com/dotnet/fsharp/language-reference/"),
        ("NuGet Packages", "https://www.nuget.org/"),
    ],
    "gdscript": [
        ("GDScript Reference", "https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/"),
        ("Godot Class Reference", "https://docs.godotengine.org/en/stable/classes/"),
        ("Godot Asset Library", "https://godotengine.org/asset-library/asset"),
    ],
    "gleam": [
        ("Gleam Documentation", "https://gleam.run/documentation/"),
        ("Gleam Language Tour", "https://tour.gleam.run/"),
        ("Gleam Packages", "https://packages.gleam.run/"),
    ],
    "glsl": [
        ("OpenGL Shading Language", "https://www.khronos.org/opengl/wiki/OpenGL_Shading_Language"),
        ("OpenGL Registry", "https://registry.khronos.org/OpenGL/"),
        ("glslang Validator", "https://github.com/KhronosGroup/glslang"),
    ],
    "go": [
        ("Go Documentation", "https://go.dev/doc/"),
        ("Go Language Specification", "https://go.dev/ref/spec"),
        ("Go Packages", "https://pkg.go.dev/"),
    ],
    "groovy": [
        ("Groovy Documentation", "https://groovy-lang.org/documentation.html"),
        ("Groovy Language Specification", "https://groovy-lang.org/syntax.html"),
        ("Gradle Groovy DSL", "https://docs.gradle.org/current/dsl/"),
    ],
    "hack": [
        ("Hack and HHVM Documentation", "https://docs.hhvm.com/"),
        ("Hack Quick Start", "https://docs.hhvm.com/hack/getting-started/quick-start/"),
        ("Hack Function References", "https://docs.hhvm.com/hack/functions/function-references/"),
    ],
    "haskell": [
        ("Haskell Documentation", "https://www.haskell.org/documentation/"),
        ("Haskell 2010 Report", "https://www.haskell.org/onlinereport/haskell2010/"),
        ("Hackage", "https://hackage.haskell.org/"),
    ],
    "hcl": [
        ("Terraform Configuration Language", "https://developer.hashicorp.com/terraform/language"),
        ("HCL GitHub", "https://github.com/hashicorp/hcl"),
        ("Terraform Registry", "https://registry.terraform.io/"),
    ],
    "hlsl": [
        ("HLSL Documentation", "https://learn.microsoft.com/windows/win32/direct3dhlsl/dx-graphics-hlsl"),
        ("HLSL Language Reference", "https://learn.microsoft.com/windows/win32/direct3dhlsl/dx-graphics-hlsl-reference"),
        ("DirectX Shader Compiler", "https://github.com/microsoft/DirectXShaderCompiler"),
    ],
    "java": [
        ("Java Documentation", "https://docs.oracle.com/en/java/"),
        ("Java Language Specification", "https://docs.oracle.com/javase/specs/"),
        ("Maven Central", "https://central.sonatype.com/"),
    ],
    "javascript": [
        ("ECMAScript Specification", "https://tc39.es/ecma262/"),
        ("MDN JavaScript Guide", "https://developer.mozilla.org/docs/Web/JavaScript"),
        ("npm Registry", "https://www.npmjs.com/"),
    ],
    "jsonnet": [
        ("Jsonnet Documentation", "https://jsonnet.org/learning/tutorial.html"),
        ("Jsonnet Language Reference", "https://jsonnet.org/ref/language.html"),
        ("Jsonnet GitHub", "https://github.com/google/jsonnet"),
    ],
    "julia": [
        ("Julia Documentation", "https://docs.julialang.org/"),
        ("Julia Manual", "https://docs.julialang.org/en/v1/manual/getting-started/"),
        ("Julia Packages", "https://juliahub.com/"),
    ],
    "kotlin": [
        ("Kotlin Documentation", "https://kotlinlang.org/docs/home.html"),
        ("Kotlin Language Specification", "https://kotlinlang.org/spec/"),
        ("Kotlin Gradle Plugin", "https://kotlinlang.org/docs/gradle-configure-project.html"),
    ],
    "lean": [
        ("Lean Documentation", "https://lean-lang.org/documentation/"),
        ("Lean Reference Manual", "https://lean-lang.org/doc/reference/latest/"),
        ("Lake Build System", "https://github.com/leanprover/lake"),
    ],
    "lisp-common-lisp": [
        ("Common Lisp HyperSpec", "https://www.lispworks.com/documentation/HyperSpec/Front/"),
        ("Common Lisp Standard", "https://www.lispworks.com/documentation/HyperSpec/"),
        ("Quicklisp", "https://www.quicklisp.org/beta/"),
    ],
    "lua": [
        ("Lua Documentation", "https://www.lua.org/docs.html"),
        ("Lua Reference Manual", "https://www.lua.org/manual/5.4/"),
        ("LuaRocks", "https://luarocks.org/"),
    ],
    "matlab": [
        ("MATLAB Documentation", "https://www.mathworks.com/help/matlab/"),
        ("MATLAB Language Fundamentals", "https://www.mathworks.com/help/matlab/language-fundamentals.html"),
        ("MATLAB Add-Ons", "https://www.mathworks.com/matlabcentral/fileexchange/"),
    ],
    "mojo": [
        ("Mojo Manual", "https://docs.modular.com/mojo/manual/"),
        ("Mojo Standard Library", "https://docs.modular.com/stable/mojo/stdlib/"),
        ("Magic Package Manager", "https://docs.modular.com/magic/"),
    ],
    "move": [
        ("Move Book", "https://move-language.github.io/move/"),
        ("Move Modules and Scripts", "https://move-language.github.io/move/modules-and-scripts.html"),
        ("Sui Move", "https://docs.sui.io/concepts/sui-move-concepts"),
    ],
    "nim": [
        ("Nim Manual", "https://nim-lang.org/docs/manual.html"),
        ("Nim Standard Library", "https://nim-lang.org/docs/lib.html"),
        ("Nimble Package Manager", "https://github.com/nim-lang/nimble"),
    ],
    "objective-c": [
        ("Objective-C Documentation", "https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/ProgrammingWithObjectiveC/Introduction/Introduction.html"),
        ("Objective-C Runtime", "https://developer.apple.com/documentation/objectivec"),
        ("Swift Package Manager", "https://www.swift.org/package-manager/"),
    ],
    "ocaml": [
        ("OCaml Documentation", "https://ocaml.org/docs"),
        ("OCaml Manual", "https://ocaml.org/manual/"),
        ("opam", "https://opam.ocaml.org/"),
    ],
    "opencl-c": [
        ("OpenCL Registry", "https://registry.khronos.org/OpenCL/"),
        ("OpenCL C Specification", "https://registry.khronos.org/OpenCL/specs/"),
        ("OpenCL SDK", "https://github.com/KhronosGroup/OpenCL-SDK"),
    ],
    "perl": [
        ("Perl Documentation", "https://perldoc.perl.org/"),
        ("perlsyn", "https://perldoc.perl.org/perlsyn"),
        ("CPAN", "https://www.cpan.org/"),
    ],
    "php": [
        ("PHP Manual", "https://www.php.net/manual/en/"),
        ("PHP Language Reference", "https://www.php.net/manual/en/langref.php"),
        ("Packagist", "https://packagist.org/"),
    ],
    "pl-sql": [
        ("PL/SQL Language Reference", "https://docs.oracle.com/en/database/oracle/oracle-database/23/lnpls/"),
        ("Oracle Database Documentation", "https://docs.oracle.com/en/database/oracle/oracle-database/"),
        ("Oracle SQL Developer", "https://www.oracle.com/database/sqldeveloper/"),
    ],
    "powershell": [
        ("PowerShell Documentation", "https://learn.microsoft.com/powershell/"),
        ("PowerShell Language Specification", "https://learn.microsoft.com/powershell/scripting/lang-spec/chapter-01"),
        ("PowerShell Gallery", "https://www.powershellgallery.com/"),
    ],
    "prolog": [
        ("SWI-Prolog Documentation", "https://www.swi-prolog.org/pldoc/doc_for?object=manual"),
        ("ISO Prolog", "https://www.iso.org/standard/21413.html"),
        ("SWI-Prolog Packs", "https://www.swi-prolog.org/pack/list"),
    ],
    "python": [
        ("Python Documentation", "https://docs.python.org/3/"),
        ("Python Language Reference", "https://docs.python.org/3/reference/"),
        ("PyPI", "https://pypi.org/"),
    ],
    "r": [
        ("R Manuals", "https://cran.r-project.org/manuals.html"),
        ("R Language Definition", "https://cran.r-project.org/doc/manuals/r-release/R-lang.html"),
        ("CRAN Packages", "https://cran.r-project.org/web/packages/"),
    ],
    "racket": [
        ("Racket Documentation", "https://docs.racket-lang.org/"),
        ("Racket Reference", "https://docs.racket-lang.org/reference/"),
        ("Racket Package Catalog", "https://pkgs.racket-lang.org/"),
    ],
    "ruby": [
        ("Ruby Documentation", "https://www.ruby-lang.org/en/documentation/"),
        ("Ruby Reference", "https://docs.ruby-lang.org/en/master/"),
        ("RubyGems", "https://rubygems.org/"),
    ],
    "rust": [
        ("Rust Documentation", "https://www.rust-lang.org/learn"),
        ("Rust Reference", "https://doc.rust-lang.org/reference/"),
        ("crates.io", "https://crates.io/"),
    ],
    "sas": [
        ("SAS Documentation", "https://documentation.sas.com/"),
        ("SAS Support Documentation", "https://support.sas.com/en/documentation.html"),
        ("SAS Viya Workbench", "https://www.sas.com/en_us/software/viya/workbench.html"),
    ],
    "scala": [
        ("Scala Documentation", "https://docs.scala-lang.org/"),
        ("Scala 3 Reference", "https://docs.scala-lang.org/scala3/reference/"),
        ("Scaladex", "https://index.scala-lang.org/"),
    ],
    "smalltalk": [
        ("Pharo Documentation", "https://pharo.org/documentation"),
        ("Pharo Book", "https://books.pharo.org/"),
        ("Pharo Project", "https://pharo.org/"),
    ],
    "solidity": [
        ("Solidity Documentation", "https://docs.soliditylang.org/"),
        ("Solidity Language Grammar", "https://docs.soliditylang.org/en/latest/grammar.html"),
        ("Foundry Book", "https://book.getfoundry.sh/"),
    ],
    "sql": [
        ("SQL Standard", "https://www.iso.org/standard/76583.html"),
        ("PostgreSQL SQL Commands", "https://www.postgresql.org/docs/current/sql-commands.html"),
        ("SQLite Documentation", "https://www.sqlite.org/docs.html"),
    ],
    "stata": [
        ("Stata Documentation", "https://www.stata.com/features/documentation/"),
        ("Stata Base Reference Manual", "https://www.stata.com/manuals/"),
        ("Stata Journal", "https://www.stata-journal.com/"),
    ],
    "swift": [
        ("Swift Documentation", "https://www.swift.org/documentation/"),
        ("Swift Book", "https://docs.swift.org/swift-book/documentation/the-swift-programming-language/"),
        ("Swift Package Manager", "https://www.swift.org/package-manager/"),
    ],
    "t-sql": [
        ("Transact-SQL Reference", "https://learn.microsoft.com/sql/t-sql/language-reference"),
        ("SQL Server Documentation", "https://learn.microsoft.com/sql/sql-server/"),
        ("sqlcmd Utility", "https://learn.microsoft.com/sql/tools/sqlcmd/sqlcmd-utility"),
    ],
    "tcl": [
        ("Tcl Documentation", "https://www.tcl-lang.org/doc/"),
        ("Tcl Commands", "https://www.tcl-lang.org/man/tcl8.6/TclCmd/contents.htm"),
        ("Tcler's Wiki", "https://wiki.tcl-lang.org/"),
    ],
    "typescript": [
        ("TypeScript Documentation", "https://www.typescriptlang.org/docs/"),
        ("TypeScript Handbook", "https://www.typescriptlang.org/docs/handbook/intro.html"),
        ("npm Registry", "https://www.npmjs.com/"),
    ],
    "vba": [
        ("VBA Documentation", "https://learn.microsoft.com/office/vba/api/overview/"),
        ("VBA Language Reference", "https://learn.microsoft.com/office/vba/language/reference/user-interface-help/visual-basic-language-reference"),
        ("Office Scripts Documentation", "https://learn.microsoft.com/office/dev/scripts/"),
    ],
    "verilog-systemverilog": [
        ("Accellera Standards", "https://accellera.org/downloads/standards"),
        ("Verilog Standard", "https://www.accellera.org/downloads/standards/v-ams"),
        ("Verilator Documentation", "https://verilator.org/guide/latest/"),
    ],
    "vhdl": [
        ("VHDL Standard", "https://standards.ieee.org/ieee/1076/"),
        ("GHDL Documentation", "https://ghdl.github.io/ghdl/"),
        ("IEEE Standards Association", "https://standards.ieee.org/"),
    ],
    "visual-basic-dotnet": [
        ("Visual Basic Documentation", "https://learn.microsoft.com/dotnet/visual-basic/"),
        ("Visual Basic Language Reference", "https://learn.microsoft.com/dotnet/visual-basic/language-reference/"),
        (".NET CLI", "https://learn.microsoft.com/dotnet/core/tools/"),
    ],
    "wat": [
        ("WebAssembly Specification", "https://webassembly.github.io/spec/core/"),
        ("WebAssembly Text Format", "https://developer.mozilla.org/docs/WebAssembly/Understanding_the_text_format"),
        ("WABT Tools", "https://github.com/WebAssembly/wabt"),
    ],
    "wolfram-language": [
        ("Wolfram Language Documentation", "https://reference.wolfram.com/language/"),
        ("Wolfram Language Guide", "https://www.wolfram.com/language/"),
        ("Wolfram Function Repository", "https://resources.wolframcloud.com/FunctionRepository/"),
    ],
    "yaml": [
        ("YAML Specification", "https://yaml.org/spec/"),
        ("YAML Official Site", "https://yaml.org/"),
        ("Kubernetes YAML Reference", "https://kubernetes.io/docs/reference/kubernetes-api/"),
    ],
    "zig": [
        ("Zig Documentation", "https://ziglang.org/documentation/master/"),
        ("Zig Language Reference", "https://ziglang.org/documentation/master/#Introduction"),
        ("Zig Package Manager", "https://ziglang.org/learn/build-system/"),
    ],
}


EXAMPLES = {
    "python": ("python", """from pathlib import Path
import csv
from collections import Counter

def summarize_orders(path: Path) -> None:
    rows = csv.DictReader(path.open(newline=""))
    revenue_by_region: Counter[str] = Counter()
    for row in rows:
        region = row["region"].strip().lower()
        revenue_by_region[region] += int(row["amount"])

    for region, revenue in revenue_by_region.most_common():
        print(f"{region:12} {revenue:>10,}")

summarize_orders(Path("orders.csv"))"""),
    "javascript": ("javascript", """const endpoint = "/api/orders";

async function loadOpenOrders() {
  const response = await fetch(endpoint);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const orders = await response.json();

  return orders
    .filter((order) => order.status === "open")
    .map((order) => ({
      id: order.id,
      total: Number(order.total),
      label: `${order.customer} / $${order.total}`,
    }));
}

loadOpenOrders().then(console.table).catch(console.error);"""),
    "typescript": ("typescript", """type Order = { id: string; total: number; status: "open" | "paid" | "void" };

function revenueReport(orders: Order[]) {
  const paid = orders.filter((order) => order.status === "paid");
  const total = paid.reduce((sum, order) => sum + order.total, 0);

  return {
    count: paid.length,
    total,
    average: paid.length === 0 ? 0 : total / paid.length,
  };
}

const report = revenueReport([
  { id: "A-100", total: 120_000, status: "paid" },
  { id: "A-101", total: 70_000, status: "open" },
]);
console.log(report);"""),
    "sql": ("sql", """WITH monthly_revenue AS (
  SELECT
    date_trunc('month', paid_at) AS month,
    region,
    SUM(amount) AS revenue
  FROM orders
  WHERE status = 'paid'
  GROUP BY 1, 2
)
SELECT
  month,
  region,
  revenue,
  RANK() OVER (PARTITION BY month ORDER BY revenue DESC) AS rank_in_month
FROM monthly_revenue
ORDER BY month DESC, rank_in_month;"""),
    "java": ("java", """import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

record Order(String region, int amount, boolean paid) {}

public class RevenueReport {
    public static Map<String, Integer> revenueByRegion(List<Order> orders) {
        return orders.stream()
            .filter(Order::paid)
            .collect(Collectors.groupingBy(
                Order::region,
                Collectors.summingInt(Order::amount)
            ));
    }
}"""),
    "csharp": ("csharp", """using System;
using System.Collections.Generic;
using System.Linq;

record Order(string Region, decimal Amount, bool Paid);

var orders = new List<Order> {
    new("apac", 120_000m, true),
    new("emea", 90_000m, true),
    new("apac", 30_000m, false)
};

var report = orders
    .Where(order => order.Paid)
    .GroupBy(order => order.Region)
    .Select(group => new { Region = group.Key, Revenue = group.Sum(x => x.Amount) });

foreach (var row in report)
    Console.WriteLine($"{row.Region}: {row.Revenue:N0}");"""),
    "c": ("c", """#include <stdio.h>
#include <stdint.h>

uint32_t crc32_step(uint32_t crc, const unsigned char *buf, size_t len) {
    while (len--) {
        crc ^= *buf++;
        for (int bit = 0; bit < 8; bit++) {
            uint32_t mask = -(crc & 1u);
            crc = (crc >> 1) ^ (0xEDB88320u & mask);
        }
    }
    return crc;
}

int main(void) {
    const unsigned char payload[] = "firmware-block";
    printf("%08x\\n", crc32_step(0xffffffffu, payload, sizeof payload - 1));
}"""),
    "cplusplus": ("cpp", """#include <algorithm>
#include <iostream>
#include <ranges>
#include <string>
#include <vector>

struct Order { std::string region; int amount; bool paid; };

int main() {
    std::vector<Order> orders{{"apac", 120}, {"emea", 90}, {"apac", 30, false}};
    auto paid = orders | std::views::filter([](const Order& o) { return o.paid; });

    int total = 0;
    for (const auto& order : paid) total += order.amount;

    std::cout << "paid revenue=" << total << "\\n";
}"""),
    "go": ("go", """package main

import (
    "context"
    "fmt"
    "net/http"
    "time"
)

func probe(ctx context.Context, url string) error {
    req, _ := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
    res, err := http.DefaultClient.Do(req)
    if err != nil {
        return err
    }
    defer res.Body.Close()
    fmt.Println(url, res.StatusCode)
    return nil
}

func main() {
    ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
    defer cancel()
    _ = probe(ctx, "https://example.com/health")
}"""),
    "rust": ("rust", """use std::collections::HashMap;

#[derive(Debug)]
struct Order {
    region: String,
    amount: i64,
    paid: bool,
}

fn revenue_by_region(orders: &[Order]) -> HashMap<&str, i64> {
    let mut report = HashMap::new();
    for order in orders.iter().filter(|order| order.paid) {
        *report.entry(order.region.as_str()).or_insert(0) += order.amount;
    }
    report
}"""),
    "php": ("php", """<?php
$orders = [
    ["region" => "apac", "amount" => 120000, "paid" => true],
    ["region" => "emea", "amount" => 90000, "paid" => true],
    ["region" => "apac", "amount" => 30000, "paid" => false],
];

$report = [];
foreach ($orders as $order) {
    if (!$order["paid"]) {
        continue;
    }
    $report[$order["region"]] = ($report[$order["region"]] ?? 0) + $order["amount"];
}

arsort($report);
print_r($report);"""),
    "kotlin": ("kotlin", """import kotlinx.coroutines.*

data class Order(val id: String, val total: Int, val paid: Boolean)

suspend fun fetchOrders(): List<Order> = coroutineScope {
    listOf(
        async { Order("A-100", 120_000, true) },
        async { Order("A-101", 70_000, false) }
    ).awaitAll()
}

fun main() = runBlocking {
    val revenue = fetchOrders()
        .filter { it.paid }
        .sumOf { it.total }
    println("paid revenue=$revenue")
}"""),
    "swift": ("swift", """import Foundation

struct Order: Decodable {
    let id: String
    let total: Decimal
    let paid: Bool
}

func paidRevenue(from data: Data) throws -> Decimal {
    let orders = try JSONDecoder().decode([Order].self, from: data)
    return orders
        .filter(\\.paid)
        .map(\\.total)
        .reduce(0, +)
}"""),
    "dart": ("dart", """class Order {
  Order(this.id, this.total, this.paid);
  final String id;
  final int total;
  final bool paid;
}

void main() {
  final orders = [
    Order("A-100", 120000, true),
    Order("A-101", 70000, false),
  ];

  final revenue = orders
      .where((order) => order.paid)
      .fold<int>(0, (sum, order) => sum + order.total);
  print("paid revenue=$revenue");
}"""),
    "ruby": ("ruby", """orders = [
  { region: "apac", amount: 120_000, paid: true },
  { region: "emea", amount: 90_000, paid: true },
  { region: "apac", amount: 30_000, paid: false }
]

report = orders
  .select { |order| order[:paid] }
  .group_by { |order| order[:region] }
  .transform_values { |rows| rows.sum { |order| order[:amount] } }

report.sort_by { |_region, revenue| -revenue }.each do |region, revenue|
  puts "#{region}: #{revenue}"
end"""),
    "r": ("r", """orders <- data.frame(
  region = c("apac", "emea", "apac"),
  amount = c(120000, 90000, 30000),
  paid = c(TRUE, TRUE, FALSE)
)

paid_orders <- subset(orders, paid == TRUE)
report <- aggregate(amount ~ region, paid_orders, sum)
report <- report[order(-report$amount), ]

print(report)
plot(report$amount, names.arg = report$region, type = "h")"""),
    "bash-shell": ("bash", """#!/usr/bin/env bash
set -euo pipefail

log_file="${1:-access.log}"
threshold="${ERROR_THRESHOLD:-10}"

errors=$(awk '$9 >= 500 { count++ } END { print count + 0 }' "$log_file")
top_path=$(awk '{ paths[$7]++ } END {
  for (path in paths) print paths[path], path
}' "$log_file" | sort -nr | head -1)

printf '5xx_count=%s\\n' "$errors"
printf 'top_path=%s\\n' "$top_path"

if (( errors > threshold )); then
  exit 2
fi"""),
    "powershell": ("powershell", """param(
    [string]$LogPath = ".\\access.log",
    [int]$Threshold = 10
)

$rows = Get-Content $LogPath | ForEach-Object {
    $parts = $_ -split "\\s+"
    [pscustomobject]@{
        Path = $parts[6]
        Status = [int]$parts[8]
    }
}

$errors = @($rows | Where-Object Status -ge 500)
$topPath = $rows | Group-Object Path | Sort-Object Count -Descending | Select-Object -First 1
Write-Host "5xx_count=$($errors.Count)"
Write-Host "top_path=$($topPath.Name)"
if ($errors.Count -gt $Threshold) { exit 2 }"""),
    "scala": ("scala", """case class Order(region: String, amount: BigDecimal, paid: Boolean)

@main def revenueReport(): Unit =
  val orders = List(
    Order("apac", BigDecimal(120000), paid = true),
    Order("emea", BigDecimal(90000), paid = true),
    Order("apac", BigDecimal(30000), paid = false)
  )

  val report = orders
    .filter(_.paid)
    .groupMapReduce(_.region)(_.amount)(_ + _)

  report.toList
    .sortBy((_, revenue) => -revenue)
    .foreach((region, revenue) => println(s"$region: $revenue"))"""),
    "lua": ("lua", """local orders = {
  { region = "apac", amount = 120000, paid = true },
  { region = "emea", amount = 90000, paid = true },
  { region = "apac", amount = 30000, paid = false },
}

local report = {}
for _, order in ipairs(orders) do
  if order.paid then
    report[order.region] = (report[order.region] or 0) + order.amount
  end
end

for region, revenue in pairs(report) do
  print(region, revenue)
end"""),
    "objective-c": ("objective-c", """#import <Foundation/Foundation.h>

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        NSArray *orders = @[
            @{@"region": @"apac", @"amount": @120000, @"paid": @YES},
            @{@"region": @"emea", @"amount": @90000, @"paid": @YES}
        ];
        NSMutableDictionary *report = [NSMutableDictionary dictionary];
        for (NSDictionary *order in orders) {
            if (![order[@"paid"] boolValue]) continue;
            NSString *region = order[@"region"];
            NSNumber *current = report[region] ?: @0;
            report[region] = @([current integerValue] + [order[@"amount"] integerValue]);
        }
        NSLog(@"%@", report);
    }
}"""),
    "perl": ("perl", """use strict;
use warnings;
use feature 'say';

my @orders = (
  { region => 'apac', amount => 120000, paid => 1 },
  { region => 'emea', amount => 90000, paid => 1 },
  { region => 'apac', amount => 30000, paid => 0 },
);

my %report;
for my $order (@orders) {
  next unless $order->{paid};
  $report{$order->{region}} += $order->{amount};
}

say "$_: $report{$_}" for sort keys %report;"""),
    "groovy": ("groovy", """def orders = [
  [region: 'apac', amount: 120000, paid: true],
  [region: 'emea', amount: 90000, paid: true],
  [region: 'apac', amount: 30000, paid: false]
]

def report = orders
  .findAll { it.paid }
  .groupBy { it.region }
  .collectEntries { region, rows ->
    [region, rows.sum { it.amount }]
  }

println report"""),
    "visual-basic-dotnet": ("vbnet", """Imports System
Imports System.Linq

Module Program
    Record Order(String Region, Decimal Amount, Boolean Paid)

    Sub Main()
        Dim orders = {
            New Order("apac", 120000D, True),
            New Order("emea", 90000D, True)
        }

        Dim report = From order In orders
                     Where order.Paid
                     Group order By order.Region Into Revenue = Sum(order.Amount)

        For Each row In report
            Console.WriteLine($"{row.Region}: {row.Revenue}")
        Next
    End Sub
End Module"""),
    "vba": ("vb", """Sub SummarizeRevenue()
    Dim rows As Variant
    rows = Range("A2:C100").Value

    Dim report As Object
    Set report = CreateObject("Scripting.Dictionary")

    Dim i As Long
    For i = 1 To UBound(rows, 1)
        If rows(i, 3) = "paid" Then
            report(rows(i, 1)) = report(rows(i, 1)) + rows(i, 2)
        End If
    Next i

    Range("E2").Resize(report.Count, 1).Value = WorksheetFunction.Transpose(report.Keys)
    Range("F2").Resize(report.Count, 1).Value = WorksheetFunction.Transpose(report.Items)
End Sub"""),
    "matlab": ("matlab", """orders = table( ...
    ["apac"; "emea"; "apac"], ...
    [120000; 90000; 30000], ...
    [true; true; false], ...
    'VariableNames', ["Region", "Amount", "Paid"]);

paidOrders = orders(orders.Paid, :);
report = groupsummary(paidOrders, "Region", "sum", "Amount");
report = sortrows(report, "sum_Amount", "descend");

disp(report)
bar(categorical(report.Region), report.sum_Amount)
ylabel("Paid revenue")"""),
    "julia": ("julia", """using DataFrames, Statistics

orders = DataFrame(
    region = ["apac", "emea", "apac"],
    amount = [120000, 90000, 30000],
    paid = [true, true, false],
)

paid = filter(:paid => identity, orders)
report = combine(groupby(paid, :region), :amount => sum => :revenue)
sort!(report, :revenue, rev=true)

println(report)
println("average=", mean(report.revenue))"""),
    "sas": ("sas", """data orders;
  input region $ amount paid $;
  datalines;
apac 120000 yes
emea 90000 yes
apac 30000 no
;
run;

proc sql;
  create table revenue as
  select region, sum(amount) as revenue
  from orders
  where paid = 'yes'
  group by region
  order by revenue desc;
quit;

proc print data=revenue; run;"""),
    "stata": ("stata", """clear
input str8 region amount str4 paid
"apac" 120000 "yes"
"emea" 90000 "yes"
"apac" 30000 "no"
end

keep if paid == "yes"
collapse (sum) revenue=amount, by(region)
gsort -revenue

list, clean
graph bar revenue, over(region) title("Paid revenue by region")"""),
    "wolfram-language": ("wolfram", """orders = {
  <|"Region" -> "apac", "Amount" -> 120000, "Paid" -> True|>,
  <|"Region" -> "emea", "Amount" -> 90000, "Paid" -> True|>,
  <|"Region" -> "apac", "Amount" -> 30000, "Paid" -> False|>
};

paid = Select[orders, #Paid &];
report = GroupBy[paid, #Region &, Total[#Amount & /@ #] &];
Dataset[KeySortBy[report, -# &]]

BarChart[Values[report], ChartLabels -> Keys[report]]"""),
    "fortran": ("fortran", """program revenue_report
  implicit none
  integer, parameter :: n = 3
  character(len=8) :: region(n) = [character(len=8) :: "apac", "emea", "apac"]
  integer :: amount(n) = [120000, 90000, 30000]
  logical :: paid(n) = [.true., .true., .false.]
  integer :: i, apac, emea

  apac = 0; emea = 0
  do i = 1, n
    if (.not. paid(i)) cycle
    select case (trim(region(i)))
    case ("apac"); apac = apac + amount(i)
    case ("emea"); emea = emea + amount(i)
    end select
  end do

  print *, "apac", apac
  print *, "emea", emea
end program revenue_report"""),
    "assembly": ("asm", """global _start
section .data
    msg db "health=ok", 10
    len equ $ - msg

section .text
_start:
    mov rax, 1          ; sys_write
    mov rdi, 1          ; stdout
    mov rsi, msg
    mov rdx, len
    syscall

    mov rax, 60         ; sys_exit
    xor rdi, rdi
    syscall"""),
    "zig": ("zig", """const std = @import("std");

const Order = struct {
    region: []const u8,
    amount: i64,
    paid: bool,
};

pub fn main() !void {
    const orders = [_]Order{
        .{ .region = "apac", .amount = 120000, .paid = true },
        .{ .region = "emea", .amount = 90000, .paid = true },
    };

    var total: i64 = 0;
    for (orders) |order| {
        if (order.paid) total += order.amount;
    }
    try std.io.getStdOut().writer().print("revenue={}\\n", .{total});
}"""),
    "ada": ("ada", """with Ada.Text_IO; use Ada.Text_IO;

procedure Revenue_Report is
   type Order is record
      Region : String (1 .. 4);
      Amount : Integer;
      Paid   : Boolean;
   end record;

   Orders : constant array (1 .. 2) of Order :=
     ((Region => "apac", Amount => 120000, Paid => True),
      (Region => "emea", Amount => 90000, Paid => True));
   Total : Integer := 0;
begin
   for O of Orders loop
      if O.Paid then
         Total := Total + O.Amount;
      end if;
   end loop;
   Put_Line ("paid revenue=" & Integer'Image (Total));
end Revenue_Report;"""),
    "cobol": ("cobol", """IDENTIFICATION DIVISION.
PROGRAM-ID. REVENUE-REPORT.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 ORDER-AMOUNT PIC 9(6) VALUE 120000.
01 TOTAL-REVENUE PIC 9(8) VALUE 0.
01 ORDER-PAID PIC X VALUE "Y".
PROCEDURE DIVISION.
    IF ORDER-PAID = "Y"
        ADD ORDER-AMOUNT TO TOTAL-REVENUE
    END-IF
    DISPLAY "PAID REVENUE=" TOTAL-REVENUE
    STOP RUN."""),
    "delphi-object-pascal": ("pascal", """type
  TOrder = record
    Region: string;
    Amount: Currency;
    Paid: Boolean;
  end;

var
  Orders: array[0..1] of TOrder;
  Total: Currency;
  Order: TOrder;
begin
  Orders[0].Region := 'apac';
  Orders[0].Amount := 120000;
  Orders[0].Paid := True;
  Total := 0;
  for Order in Orders do
    if Order.Paid then
      Total := Total + Order.Amount;
  Writeln('paid revenue=', Total:0:0);
end."""),
    "abap": ("abap", """TYPES: BEGIN OF ty_order,
         region TYPE string,
         amount TYPE i,
         paid   TYPE abap_bool,
       END OF ty_order.

DATA orders TYPE STANDARD TABLE OF ty_order WITH EMPTY KEY.
orders = VALUE #(
  ( region = 'APAC' amount = 120000 paid = abap_true )
  ( region = 'EMEA' amount = 90000 paid = abap_true ) ).

DATA(total) = REDUCE i(
  INIT sum = 0
  FOR order IN orders WHERE ( paid = abap_true )
  NEXT sum = sum + order-amount ).

cl_demo_output=>display( |Paid revenue: { total }| )."""),
    "pl-sql": ("sql", """DECLARE
  v_total NUMBER := 0;
BEGIN
  SELECT SUM(amount)
    INTO v_total
    FROM orders
   WHERE status = 'PAID'
     AND paid_at >= ADD_MONTHS(TRUNC(SYSDATE, 'MM'), -1);

  INSERT INTO revenue_audit(run_at, total_amount)
  VALUES (SYSTIMESTAMP, v_total);

  COMMIT;
  DBMS_OUTPUT.PUT_LINE('monthly revenue=' || v_total);
EXCEPTION
  WHEN OTHERS THEN
    ROLLBACK;
    RAISE;
END;"""),
    "t-sql": ("sql", """BEGIN TRANSACTION;

WITH paid AS (
  SELECT region, amount
  FROM dbo.orders WITH (READCOMMITTEDLOCK)
  WHERE status = 'PAID'
    AND paid_at >= DATEADD(day, -30, SYSUTCDATETIME())
)
INSERT INTO dbo.revenue_snapshot(region, revenue, created_at)
SELECT region, SUM(amount), SYSUTCDATETIME()
FROM paid
GROUP BY region;

COMMIT TRANSACTION;"""),
    "haskell": ("haskell", """import Data.List (foldl')
import qualified Data.Map.Strict as Map

data Order = Order { region :: String, amount :: Int, paid :: Bool }

revenueByRegion :: [Order] -> Map.Map String Int
revenueByRegion =
  foldl' addPaid Map.empty
  where
    addPaid acc order
      | paid order = Map.insertWith (+) (region order) (amount order) acc
      | otherwise = acc

main :: IO ()
main = print $ revenueByRegion [Order "apac" 120000 True, Order "emea" 90000 True]"""),
    "ocaml": ("ocaml", """module RegionMap = Map.Make(String)

type order = { region : string; amount : int; paid : bool }

let add_order report order =
  if order.paid then
    RegionMap.update order.region
      (fun value -> Some (order.amount + Option.value value ~default:0))
      report
  else report

let revenue_by_region orders =
  List.fold_left add_order RegionMap.empty orders

let () =
  let report = revenue_by_region [{ region = "apac"; amount = 120000; paid = true }] in
  RegionMap.iter (fun region revenue -> Printf.printf "%s %d\\n" region revenue) report"""),
    "fsharp": ("fsharp", """type Order = { Region: string; Amount: decimal; Paid: bool }

let orders =
    [ { Region = "apac"; Amount = 120000M; Paid = true }
      { Region = "emea"; Amount = 90000M; Paid = true }
      { Region = "apac"; Amount = 30000M; Paid = false } ]

let report =
    orders
    |> List.filter _.Paid
    |> List.groupBy _.Region
    |> List.map (fun (region, rows) -> region, rows |> List.sumBy _.Amount)

report
|> List.sortByDescending snd
|> List.iter (fun (region, revenue) -> printfn "%s: %M" region revenue)"""),
    "erlang": ("erlang", """-module(revenue_report).
-export([run/0]).

run() ->
    Orders = [
        #{region => <<"apac">>, amount => 120000, paid => true},
        #{region => <<"emea">>, amount => 90000, paid => true},
        #{region => <<"apac">>, amount => 30000, paid => false}
    ],
    Report = lists:foldl(fun add_order/2, #{}, Orders),
    io:format("~p~n", [Report]).

add_order(#{paid := false}, Report) -> Report;
add_order(#{region := Region, amount := Amount}, Report) ->
    maps:update_with(Region, fun(Value) -> Value + Amount end, Amount, Report)."""),
    "elixir": ("elixir", """orders = [
  %{region: "apac", amount: 120_000, paid: true},
  %{region: "emea", amount: 90_000, paid: true},
  %{region: "apac", amount: 30_000, paid: false}
]

report =
  orders
  |> Enum.filter(& &1.paid)
  |> Enum.group_by(& &1.region)
  |> Map.new(fn {region, rows} ->
    {region, Enum.sum(Enum.map(rows, & &1.amount))}
  end)

IO.inspect(report, label: "paid revenue")"""),
    "lisp-common-lisp": ("lisp", """(defparameter *orders*
  '((:region "apac" :amount 120000 :paid t)
    (:region "emea" :amount 90000 :paid t)
    (:region "apac" :amount 30000 :paid nil)))

(defun revenue-by-region (orders)
  (let ((report (make-hash-table :test 'equal)))
    (dolist (order orders report)
      (when (getf order :paid)
        (incf (gethash (getf order :region) report 0)
              (getf order :amount))))))

(maphash (lambda (region revenue)
           (format t "~a: ~a~%" region revenue))
         (revenue-by-region *orders*))"""),
    "clojure": ("clojure", """(def orders
  [{:region "apac" :amount 120000 :paid? true}
   {:region "emea" :amount 90000 :paid? true}
   {:region "apac" :amount 30000 :paid? false}])

(defn revenue-by-region [orders]
  (->> orders
       (filter :paid?)
       (group-by :region)
       (map (fn [[region rows]]
              [region (reduce + (map :amount rows))]))
       (into {})))

(println (revenue-by-region orders))"""),
    "prolog": ("prolog", """order(apac, 120000, paid).
order(emea, 90000, paid).
order(apac, 30000, open).

paid_amount(Region, Amount) :-
    order(Region, Amount, paid).

revenue_by_region(Region, Revenue) :-
    setof(Amount, paid_amount(Region, Amount), Amounts),
    sum_list(Amounts, Revenue).

top_region(Region, Revenue) :-
    revenue_by_region(Region, Revenue),
    \\+ (revenue_by_region(_, Other), Other > Revenue)."""),
    "gdscript": ("gdscript", """extends Node

var orders := [
    {"region": "apac", "amount": 120000, "paid": true},
    {"region": "emea", "amount": 90000, "paid": true},
    {"region": "apac", "amount": 30000, "paid": false},
]

func _ready() -> void:
    var report := {}
    for order in orders:
        if not order.paid:
            continue
        report[order.region] = report.get(order.region, 0) + order.amount

    for region in report.keys():
        print("%s: %d" % [region, report[region]])"""),
    "hlsl": ("hlsl", """cbuffer Scene : register(b0)
{
    float4x4 viewProjection;
    float3 lightDirection;
};

struct VSInput { float3 position : POSITION; float3 normal : NORMAL; };
struct VSOutput { float4 position : SV_Position; float light : TEXCOORD0; };

VSOutput main(VSInput input)
{
    VSOutput output;
    output.position = mul(viewProjection, float4(input.position, 1.0));
    output.light = saturate(dot(normalize(input.normal), -lightDirection));
    return output;
}"""),
    "glsl": ("glsl", """#version 330 core

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;

uniform mat4 viewProjection;
uniform vec3 lightDirection;

out float vLight;

void main() {
    gl_Position = viewProjection * vec4(position, 1.0);
    vLight = clamp(dot(normalize(normal), -lightDirection), 0.0, 1.0);
}"""),
    "cuda-c-cplusplus": ("cuda", """__global__ void saxpy(int n, float a, const float *x, float *y) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) {
        y[i] = a * x[i] + y[i];
    }
}

void launch_saxpy(int n, float a, const float *x, float *y) {
    int threads = 256;
    int blocks = (n + threads - 1) / threads;
    saxpy<<<blocks, threads>>>(n, a, x, y);
    cudaDeviceSynchronize();
}"""),
    "opencl-c": ("c", """__kernel void saxpy(
    const int n,
    const float a,
    __global const float *x,
    __global float *y)
{
    int i = get_global_id(0);
    if (i < n) {
        y[i] = a * x[i] + y[i];
    }
}"""),
    "vhdl": ("vhdl", """library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity counter is
  port (
    clk   : in  std_logic;
    reset : in  std_logic;
    value : out unsigned(7 downto 0)
  );
end entity;

architecture rtl of counter is
  signal count : unsigned(7 downto 0) := (others => '0');
begin
  process(clk)
  begin
    if rising_edge(clk) then
      if reset = '1' then count <= (others => '0');
      else count <= count + 1;
      end if;
    end if;
  end process;
  value <= count;
end architecture;"""),
    "verilog-systemverilog": ("systemverilog", """module counter #(
  parameter WIDTH = 8
) (
  input  logic clk,
  input  logic reset,
  output logic [WIDTH-1:0] value
);

always_ff @(posedge clk) begin
  if (reset) begin
    value <= '0;
  end else begin
    value <= value + 1'b1;
  end
end

endmodule"""),
    "hcl": ("hcl", """terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_s3_bucket" "logs" {
  bucket = "${var.project}-logs"
  tags = {
    Service = var.project
    Owner   = "platform"
  }
}

resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id
  versioning_configuration { status = "Enabled" }
}"""),
    "yaml": ("yaml", """apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders-api
  labels:
    app: orders-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: orders-api
  template:
    metadata:
      labels:
        app: orders-api
    spec:
      containers:
        - name: api
          image: registry.example.com/orders-api:1.4.2
          ports:
            - containerPort: 8080"""),
    "jsonnet": ("jsonnet", """local service(name, image, port) = {
  apiVersion: 'apps/v1',
  kind: 'Deployment',
  metadata: { name: name },
  spec: {
    replicas: 3,
    selector: { matchLabels: { app: name } },
    template: {
      metadata: { labels: { app: name } },
      spec: {
        containers: [{ name: name, image: image, ports: [{ containerPort: port }] }],
      },
    },
  },
};

service('orders-api', 'registry.example.com/orders-api:1.4.2', 8080)"""),
    "solidity": ("solidity", """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract Escrow {
    address public immutable buyer;
    address payable public immutable seller;
    uint256 public immutable amount;

    constructor(address payable _seller) payable {
        buyer = msg.sender;
        seller = _seller;
        amount = msg.value;
    }

    function release() external {
        require(msg.sender == buyer, "only buyer");
        seller.transfer(amount);
    }
}"""),
    "move": ("move", """module orders::escrow {
    use sui::coin::{Self, Coin};
    use sui::sui::SUI;
    use sui::transfer;
    use sui::tx_context::{Self, TxContext};

    public struct Escrow has key {
        id: UID,
        amount: Coin<SUI>,
    }

    public entry fun create(amount: Coin<SUI>, ctx: &mut TxContext) {
        let escrow = Escrow { id: object::new(ctx), amount };
        transfer::transfer(escrow, tx_context::sender(ctx));
    }
}"""),
    "apex": ("apex", """public with sharing class AccountRevenueService {
    public static Map<Id, Decimal> revenueByAccount(Set<Id> accountIds) {
        Map<Id, Decimal> result = new Map<Id, Decimal>();
        for (AggregateResult row : [
            SELECT AccountId accountId, SUM(Amount) revenue
            FROM Opportunity
            WHERE AccountId IN :accountIds AND IsWon = true
            GROUP BY AccountId
        ]) {
            result.put((Id) row.get('accountId'), (Decimal) row.get('revenue'));
        }
        return result;
    }
}"""),
    "hack": ("hack", """<?hh
type Order = shape(
  'region' => string,
  'amount' => int,
  'paid' => bool,
);

function revenue_by_region(vec<Order> $orders): dict<string, int> {
  $report = dict[];
  foreach ($orders as $order) {
    if (!$order['paid']) continue;
    $region = $order['region'];
    $report[$region] = ($report[$region] ?? 0) + $order['amount'];
  }
  return $report;
}"""),
    "nim": ("nim", """import tables

type Order = object
  region: string
  amount: int
  paid: bool

let orders = @[
  Order(region: "apac", amount: 120000, paid: true),
  Order(region: "emea", amount: 90000, paid: true)
]

var report = initTable[string, int]()
for order in orders:
  if order.paid:
    report[order.region] = report.getOrDefault(order.region) + order.amount

echo report"""),
    "crystal": ("crystal", """record Order, region : String, amount : Int32, paid : Bool

orders = [
  Order.new("apac", 120_000, true),
  Order.new("emea", 90_000, true),
  Order.new("apac", 30_000, false),
]

report = Hash(String, Int32).new(0)
orders.each do |order|
  next unless order.paid
  report[order.region] += order.amount
end

report.each { |region, revenue| puts "#{region}: #{revenue}" }"""),
    "d": ("d", """import std.stdio;
import std.algorithm;
import std.array;

struct Order {
    string region;
    int amount;
    bool paid;
}

void main() {
    auto orders = [Order("apac", 120000, true), Order("emea", 90000, true)];
    auto total = orders
        .filter!(order => order.paid)
        .map!(order => order.amount)
        .sum;
    writeln("paid revenue=", total);
}"""),
    "forth": ("forth", """: paid-revenue ( amount paid total -- total )
  rot 0<> if + else drop then ;

0 constant unpaid
1 constant paid

variable total
0 total !

120000 paid total @ paid-revenue total !
 90000 paid total @ paid-revenue total !
 30000 unpaid total @ paid-revenue total !

.( paid revenue= ) total @ . cr"""),
    "tcl": ("tcl", """set orders {
  {apac 120000 paid}
  {emea 90000 paid}
  {apac 30000 open}
}

array set report {}
foreach order $orders {
  lassign $order region amount status
  if {$status ne "paid"} {
    continue
  }
  incr report($region) $amount
}

foreach region [array names report] {
  puts "$region: $report($region)"
}"""),
    "awk": ("awk", """BEGIN {
  FS = ","
  print "region,revenue"
}
NR > 1 && $3 == "paid" {
  revenue[$1] += $2
}
END {
  for (region in revenue) {
    printf "%s,%d\\n", region, revenue[region]
  }
}"""),
    "autohotkey": ("autohotkey", """#Requires AutoHotkey v2.0

orders := [
  Map("region", "apac", "amount", 120000, "paid", true),
  Map("region", "emea", "amount", 90000, "paid", true),
  Map("region", "apac", "amount", 30000, "paid", false)
]

report := Map()
for order in orders {
  if !order["paid"]
    continue
  region := order["region"]
  report[region] := report.Get(region, 0) + order["amount"]
}

MsgBox "APAC revenue: " report.Get("apac", 0)"""),
    "mojo": ("mojo", """from collections import Dict

struct Order:
    var region: String
    var amount: Int
    var paid: Bool

fn main():
    var report = Dict[String, Int]()
    var apac = Order("apac", 120000, True)
    var emea = Order("emea", 90000, True)

    for order in List[Order](apac, emea):
        if order.paid:
            report[order.region] = report.get(order.region, 0) + order.amount

    print(report["apac"])"""),
    "carbon": ("carbon", """package RevenueReport api;

class Order {
  var region: String;
  var amount: i32;
  var paid: bool;
}

fn PaidRevenue(orders: Slice(Order)) -> i32 {
  var total: i32 = 0;
  for (order: Order in orders) {
    if (order.paid) {
      total += order.amount;
    }
  }
  return total;
}"""),
    "wat": ("wat", """(module
  (memory (export "memory") 1)
  (func (export "add_paid")
    (param $current i32)
    (param $amount i32)
    (param $paid i32)
    (result i32)
    local.get $paid
    if (result i32)
      local.get $current
      local.get $amount
      i32.add
    else
      local.get $current
    end))"""),
    "smalltalk": ("smalltalk", """| orders report |
orders := {
  Dictionary newFrom: { #region -> 'apac'. #amount -> 120000. #paid -> true }.
  Dictionary newFrom: { #region -> 'emea'. #amount -> 90000. #paid -> true }.
  Dictionary newFrom: { #region -> 'apac'. #amount -> 30000. #paid -> false } }.

report := Dictionary new.
orders do: [ :order |
  (order at: #paid) ifTrue: [
    | region current |
    region := order at: #region.
    current := report at: region ifAbsent: [ 0 ].
    report at: region put: current + (order at: #amount) ] ].

Transcript show: report printString; cr."""),
    "racket": ("racket", """#lang racket

(struct order (region amount paid?) #:transparent)

(define orders
  (list (order "apac" 120000 #t)
        (order "emea" 90000 #t)
        (order "apac" 30000 #f)))

(define (add-order report o)
  (if (order-paid? o)
      (hash-update report (order-region o)
                   (lambda (value) (+ value (order-amount o))) 0)
      report))

(define report (foldl add-order (hash) orders))
(displayln report)"""),
    "gleam": ("gleam", """import gleam/dict
import gleam/list
import gleam/io

pub type Order {
  Order(region: String, amount: Int, paid: Bool)
}

pub fn revenue_by_region(orders: List(Order)) {
  list.fold(orders, dict.new(), fn(report, order) {
    case order.paid {
      True -> dict.upsert(report, order.region, order.amount, fn(value) { value + order.amount })
      False -> report
    }
  })
}

pub fn main() {
  io.debug(revenue_by_region([Order("apac", 120000, True)]))
}"""),
    "lean": ("lean", """structure Order where
  region : String
  amount : Nat
  paid : Bool
deriving Repr

def paidRevenue (orders : List Order) : Nat :=
  orders.foldl
    (fun total order =>
      if order.paid then total + order.amount else total)
    0

#eval paidRevenue [
  { region := "apac", amount := 120000, paid := true },
  { region := "emea", amount := 90000, paid := true }
]"""),
}


def section(text: str, heading: str) -> str:
    """지정한 2단계 Markdown 섹션 본문만 추출한다."""
    pattern = rf"(?ms)^## {re.escape(heading)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def title_of(text: str) -> str:
    """언어 문서의 최상위 제목을 읽어 표시 이름으로 사용한다."""
    match = re.search(r"^# (.+)$", text, re.MULTILINE)
    if not match:
        raise ValueError("missing title")
    return match.group(1)


def list_items(text: str) -> list[str]:
    """Markdown bullet 목록을 순서 보존 리스트로 변환한다."""
    return [line[2:].strip() for line in text.splitlines() if line.startswith("- ")]


def paragraph(text: str) -> str:
    """목록이 아닌 문장 줄을 하나의 문단 문자열로 합친다."""
    return " ".join(line.strip() for line in text.splitlines() if line.strip() and not line.startswith("- "))


def before_marker(value: str, marker: str) -> str:
    """반복 생성 문구 앞부분만 남겨 기존 문장 중복을 줄인다."""
    if marker in value:
        return value.split(marker, 1)[0].strip()
    return value.strip()


def dedupe(items: list[str]) -> list[str]:
    """입력 순서를 보존하면서 중복 항목을 제거한다."""
    seen = set()
    result = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def build_doc(lang_id: str, old: str) -> str:
    """기존 언어 문서를 품질 게이트를 만족하는 표준 문서로 재구성한다."""
    title = title_of(old)
    judgement = before_marker(paragraph(section(old, "핵심 판단")), f". {title} 도입 판단").rstrip(".")
    uses = before_marker(paragraph(section(old, "사용처")), ". 실무에서는").rstrip(".")
    features = before_marker(paragraph(section(old, "특징")), ". 코드 작성 모델").rstrip(".")
    strengths = before_marker(paragraph(section(old, "장점")), ". 특히").rstrip(".")
    constraints = before_marker(paragraph(section(old, "제약")), ". 이 제약").rstrip(".")
    good = [
        item
        for item in dedupe(list_items(section(old, "적합한 프로젝트")))
        if "표준 도구와 런타임을 팀이 직접 운영" not in item
    ]
    bad = [
        item
        for item in dedupe(list_items(section(old, "부적합하거나 주의할 프로젝트")))
        if "경험자가 없는데 핵심 장애 대응" not in item
    ]
    ecosystem = dedupe(list_items(section(old, "대표 생태계와 도구")))
    learning = before_marker(paragraph(section(old, "학습 난이도와 선행 지식")), ". 입문 단계에서는").rstrip(".")
    ops = before_marker(paragraph(section(old, "운영/배포 관점")), ". 재현 가능한").rstrip(".")
    runtime = before_marker(paragraph(section(old, "타입/런타임 특성")), ". 이 특성은").rstrip(".")
    compare = list_items(section(old, "함께 비교할 언어"))[:6]
    docs = DOCS[lang_id]
    code_lang, code = EXAMPLES[lang_id]

    if not good:
        good = [f"{uses} 요구가 제품 핵심인 프로젝트.", "팀이 빌드, 테스트, 배포 흐름을 반복 가능하게 운영할 수 있는 프로젝트."]
    if not bad:
        bad = [f"{constraints} 제약이 핵심 리스크인 프로젝트.", "팀 내 운영 경험이 없고 장기 유지보수 책임이 불명확한 프로젝트."]

    doc_lines = [
        "<!-- markdownlint-disable MD013 -->",
        "",
        f"# {title}",
        "",
        "원천: `docs/PROGRAMMING_LANGUAGES_2026.md`, 기준일 2026-05-13. 최신 순위와 시장 지표는 답변 시점에 웹으로 확인한다.",
        "",
        "## 핵심 판단",
        "",
        f"{judgement}. {title} 도입 판단은 문법 선호보다 실행 환경, 기존 자산, 운영 인력의 숙련도에 더 크게 좌우된다. 제품의 주 경로가 {uses}이고, 다음 제약을 통제할 수 있다면 우선 검토할 만하다: {constraints}.",
        "",
        "## 사용처",
        "",
        f"{uses}. 실무에서는 이 범위를 넘어 모든 문제를 해결하는 범용 선택지로 보기보다, {title} 생태계가 이미 강한 플랫폼과 도구 체인에 맞춰 채택하는 편이 안정적이다. 신규 프로젝트에서는 장기 유지보수 인력과 배포 대상의 제약을 함께 확인해야 한다.",
        "",
        "## 특징",
        "",
        f"{features}. 코드 작성 모델, 빌드 방식, 런타임 제약이 프로젝트 구조에 직접 영향을 주므로 초기 설계 단계에서 테스트 전략과 패키지 관리 방식을 같이 정해야 한다.",
        "",
        "## 장점",
        "",
        f"{strengths}. 특히 기존 생태계의 표준 도구를 그대로 활용할 수 있을 때 생산성과 운영 예측 가능성이 높다. 팀이 관용구와 디버깅 방식을 익히면 같은 기능을 더 적은 접착 코드로 구현할 수 있다.",
        "",
        "## 제약",
        "",
        f"{constraints}. 이 제약은 작은 실험에서는 드러나지 않다가 배포, 성능, 보안 감사, 장기 유지보수 단계에서 비용으로 나타나는 경우가 많다. 도입 전에는 대체 언어와 운영 모델을 같이 비교해야 한다.",
        "",
        "## 적합한 프로젝트",
        "",
    ]
    doc_lines.extend(f"- {item}" for item in good)
    doc_lines.extend([
        f"- {title} 표준 도구와 런타임을 팀이 직접 운영할 수 있고, 코드 리뷰에서 언어별 관용구를 일관되게 적용할 수 있는 프로젝트.",
        "",
        "## 부적합하거나 주의할 프로젝트",
        "",
    ])
    doc_lines.extend(f"- {item}" for item in bad)
    doc_lines.extend([
        f"- {title} 경험자가 없는데 핵심 장애 대응, 성능 튜닝, 릴리스 자동화까지 동시에 요구되는 프로젝트.",
        "",
        "## 대표 생태계와 도구",
        "",
    ])
    doc_lines.extend(f"- {item}" for item in ecosystem)
    doc_lines.extend([
        "",
        "## 학습 난이도와 선행 지식",
        "",
        f"{learning}. 입문 단계에서는 문법보다 작은 프로그램을 빌드, 테스트, 포맷, 배포하는 전체 흐름을 먼저 익히는 것이 좋다. 실무 투입 전에는 오류 처리, 의존성 관리, 표준 라이브러리 사용법을 팀 규칙으로 정리해야 한다.",
        "",
        "## 운영/배포 관점",
        "",
        f"{ops}. 재현 가능한 빌드, 의존성 잠금, 런타임 버전 고정, 관측 로그 포맷을 초기에 정하지 않으면 운영 환경 차이로 인한 결함이 늘어난다.",
        "",
        "## 타입/런타임 특성",
        "",
        f"{runtime}. 이 특성은 API 경계, 테스트 범위, 병렬성 모델, 장애 격리 방식에 영향을 준다. 언어의 타입 시스템이 보장하지 않는 부분은 정적 분석, 테스트, 코드 리뷰 규칙으로 보완해야 한다.",
        "",
        "## 실사용 예제",
        "",
        "다음 예제는 이 언어를 단순 출력이 아니라 실제 업무 코드에서 자주 나오는 데이터 집계, 자동화, 런타임 제어, 또는 플랫폼 특화 작업에 적용하는 형태로 보여준다.",
        "",
        f"```{code_lang}",
        code,
        "```",
        "",
        "## 관련 문서",
        "",
    ])
    doc_lines.extend(f"- [{label}]({url})" for label, url in docs)
    doc_lines.extend([
        "",
        "## 비교 포인트",
        "",
    ])
    criteria = [
        "생태계와 채용 풀, 장기 유지보수성, 배포 환경 제약을 우선 비교한다.",
        "성능보다 생산성이 중요한지, 컴파일 시점 보장이 중요한지, 런타임 유연성이 중요한지 구분한다.",
        "표준 라이브러리와 패키지 관리가 팀의 보안·라이선스 정책에 맞는지 확인한다.",
        "기존 코드베이스와의 상호 운용, 마이그레이션 비용, 관측/디버깅 도구 성숙도를 함께 본다.",
    ]
    for idx, item in enumerate(compare):
        criterion = criteria[idx % len(criteria)]
        doc_lines.append(f"- {item}: {criterion}")
    doc_lines.extend([
        "",
        "## 함께 비교할 언어",
        "",
    ])
    doc_lines.extend(f"- {item}" for item in compare)
    doc_lines.extend([
        "",
        "## 추천 학습/도입 상황",
        "",
        f"- 제품의 핵심 경로가 {uses}이고, 팀이 {title}의 표준 빌드·테스트·배포 흐름을 문서화할 수 있을 때 도입 우선순위를 높인다.",
        f"- 다음 강점이 일정, 품질, 운영 비용 중 하나를 명확히 낮출 때 실무 채택 근거가 충분하다: {strengths}.",
        f"- 다음 제약이 핵심 리스크라면 파일럿 구현, 성능 측정, 장애 대응 연습을 거친 뒤 본격 도입한다: {constraints}.",
        "",
        "## 도입 전 체크리스트",
        "",
        "- 현재 팀이 이 언어의 빌드, 테스트, 디버깅, 배포 흐름을 문서화하고 반복 실행할 수 있는지 확인한다.",
        "- 핵심 라이브러리와 프레임워크의 유지보수 상태, 라이선스, 보안 업데이트 흐름을 확인한다.",
        "- 대체 언어와 비교해 학습 비용, 운영 리스크, 장기 인력 수급이 프로젝트 기간에 맞는지 확인한다.",
        "- 공식 문서, 언어 스펙 또는 레퍼런스, 패키지/툴링 문서를 최소 1회 확인하고 프로젝트 표준 링크로 남긴다.",
        "",
        "## 최신 확인 필요",
        "",
        "- 인기 순위, 점유율, 채용 수요, 연봉 데이터는 답변 시점의 최신 자료로 확인한다.",
        "- 최신 안정 버전, LTS 정책, 주요 프레임워크 버전은 공식 문서나 릴리스 노트로 확인한다.",
        "- 보안 권고, 패키지 생태계 상태, 플랫폼 지원 종료 여부는 프로젝트 도입 전에 별도 확인한다.",
        "",
    ])
    return "\n".join(doc_lines)


def main() -> None:
    """75개 언어 문서 전체를 재생성하고 누락된 메타데이터를 검증한다."""
    files = sorted(p for p in LANG_DIR.glob("*.md") if p.name not in {"index.md", "domains.md"})
    file_ids = {p.stem for p in files}
    missing_docs = file_ids - DOCS.keys()
    missing_examples = file_ids - EXAMPLES.keys()
    extra_docs = DOCS.keys() - file_ids
    extra_examples = EXAMPLES.keys() - file_ids
    problems = []
    if missing_docs:
        problems.append(f"missing DOCS: {sorted(missing_docs)}")
    if missing_examples:
        problems.append(f"missing EXAMPLES: {sorted(missing_examples)}")
    if extra_docs:
        problems.append(f"extra DOCS: {sorted(extra_docs)}")
    if extra_examples:
        problems.append(f"extra EXAMPLES: {sorted(extra_examples)}")
    if problems:
        raise SystemExit("\n".join(problems))

    for path in files:
        old = path.read_text(encoding="utf-8")
        path.write_text(build_doc(path.stem, old), encoding="utf-8")
    print(f"enriched {len(files)} language files")


if __name__ == "__main__":
    main()
