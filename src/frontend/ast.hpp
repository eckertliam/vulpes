#pragma once

#include "location.hpp"
#include "token.hpp"

#include <memory>
#include <optional>
#include <vector>

namespace vulpes::frontend {

// Forward declarations
struct Expr;
struct Stmt;
struct IntegerLiteral;
struct FloatLiteral;
struct StringLiteral;
struct CharLiteral;
struct BoolLiteral;
struct NullLiteral;
struct UnaryExpr;
struct BinaryExpr;
struct GroupingExpr;
struct VarExpr;
struct AssignExpr;
struct LogicalExpr;
struct CallExpr;
struct GetExpr;
struct SetExpr;
struct ExpressionStmt;
struct LetStmt;
struct ConstStmt;
struct BlockStmt;
struct IfStmt;
struct WhileStmt;
struct ForStmt;
struct ReturnStmt;
struct FunctionStmt;
struct ClassStmt;

struct AstVisitor {
  virtual ~AstVisitor() = default;
  virtual void visit(const IntegerLiteral& expr) = 0;
  virtual void visit(const FloatLiteral& expr) = 0;
  virtual void visit(const StringLiteral& expr) = 0;
  virtual void visit(const CharLiteral& expr) = 0;
  virtual void visit(const BoolLiteral& expr) = 0;
  virtual void visit(const NullLiteral& expr) = 0;
  virtual void visit(const UnaryExpr& expr) = 0;
  virtual void visit(const BinaryExpr& expr) = 0;
  virtual void visit(const GroupingExpr& expr) = 0;
  virtual void visit(const VarExpr& expr) = 0;
  virtual void visit(const AssignExpr& expr) = 0;
  virtual void visit(const LogicalExpr& expr) = 0;
  virtual void visit(const CallExpr& expr) = 0;
  virtual void visit(const GetExpr& expr) = 0;
  virtual void visit(const SetExpr& expr) = 0;
  virtual void visit(const ExpressionStmt& stmt) = 0;
  virtual void visit(const LetStmt& stmt) = 0;
  virtual void visit(const ConstStmt& stmt) = 0;
  virtual void visit(const BlockStmt& stmt) = 0;
  virtual void visit(const IfStmt& stmt) = 0;
  virtual void visit(const WhileStmt& stmt) = 0;
  virtual void visit(const ForStmt& stmt) = 0;
  virtual void visit(const ReturnStmt& stmt) = 0;
  virtual void visit(const FunctionStmt& stmt) = 0;
  virtual void visit(const ClassStmt& stmt) = 0;
};

struct AstNode {
  virtual ~AstNode() = default;
  virtual void accept(AstVisitor& visitor) const = 0;
  Location location;

 protected:
  AstNode() = default;
};

struct Expr : AstNode {};
struct Stmt : AstNode {};

struct IntegerLiteral final : Expr {
  int64_t value;

  explicit IntegerLiteral(const Token& token) {
    const std::string_view lexeme = token.lexeme();
    // TODO: handle binary and hex formats
    value = std::stoll(std::string(lexeme));
    location = token.location;
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct FloatLiteral final : Expr {
  double value;

  explicit FloatLiteral(const Token& token) {
    const std::string_view lexeme = token.lexeme();
    value = std::stod(std::string(lexeme));
    location = token.location;
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct StringLiteral final : Expr {
  std::string_view value;

  explicit StringLiteral(const Token& token) {
    const std::string_view lexeme = token.lexeme();
    // remove quote around the string
    value = lexeme.substr(1, lexeme.size() - 2);
    location = token.location;
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct CharLiteral final : Expr {
  char value;

  explicit CharLiteral(const Token& token) {
    const std::string_view lexeme = token.lexeme();
    // TODO: handle escape cases
    value = lexeme[1];
    location = token.location;
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct BoolLiteral final : Expr {
  bool value;

  explicit BoolLiteral(const Token& token) {
    value = token.lexeme() == "true";
    location = token.location;
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct NullLiteral final : Expr {
  explicit NullLiteral(const Token& token) { location = token.location; }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct UnaryExpr final : Expr {
  Token op;
  std::unique_ptr<Expr> right;

  UnaryExpr(const Token& op, std::unique_ptr<Expr> right)
      : op(op), right(std::move(right)) {
    location = op.location;
    location.end_line = this->right->location.end_line;
    location.end_column = this->right->location.end_column;
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct BinaryExpr final : Expr {
  std::unique_ptr<Expr> left;
  Token op;
  std::unique_ptr<Expr> right;

  BinaryExpr(std::unique_ptr<Expr> left, const Token& op,
             std::unique_ptr<Expr> right)
      : left(std::move(left)), op(op), right(std::move(right)) {
    location = this->left->location;
    location.end_line = this->right->location.end_line;
    location.end_column = this->right->location.end_column;
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct GroupingExpr final : Expr {
  std::unique_ptr<Expr> expr;

  explicit GroupingExpr(std::unique_ptr<Expr> expr) : expr(std::move(expr)) {
    location = this->expr->location;
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct VarExpr final : Expr {
  std::string_view name;

  explicit VarExpr(const Token& name_tok) : name(name_tok.lexeme()) {
    location = name_tok.location;
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct AssignExpr final : Expr {
  std::string_view name;
  std::unique_ptr<Expr> value;

  AssignExpr(const Token& name_tok, std::unique_ptr<Expr> value)
      : name(name_tok.lexeme()), value(std::move(value)) {
    location = name_tok.location;
    location.end_line = this->value->location.end_line;
    location.end_column = this->value->location.end_column;
  }

  AssignExpr(const VarExpr* var_expr, std::unique_ptr<Expr> value)
      : name(var_expr->name), value(std::move(value)) {
    location = var_expr->location;
    location.end_line = this->value->location.end_line;
    location.end_column = this->value->location.end_column;
  }
  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct LogicalExpr final : Expr {
  std::unique_ptr<Expr> left;
  Token op;
  std::unique_ptr<Expr> right;

  LogicalExpr(std::unique_ptr<Expr> left, const Token& op,
              std::unique_ptr<Expr> right)
      : left(std::move(left)), op(op), right(std::move(right)) {
    location = this->left->location;
    location.end_line = this->right->location.end_line;
    location.end_column = this->right->location.end_column;
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct CallExpr final : Expr {
  std::unique_ptr<Expr> callee;
  std::vector<std::unique_ptr<Expr>> arguments;

  CallExpr(std::unique_ptr<Expr> callee, const Token& paren,
           std::vector<std::unique_ptr<Expr>> arguments)
      : callee(std::move(callee)), arguments(std::move(arguments)) {
    location = this->callee->location;
    location.end_line = paren.location.end_line;
    location.end_column = paren.location.end_column;
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct GetExpr final : Expr {
  std::unique_ptr<Expr> object;
  std::string_view name;

  GetExpr(std::unique_ptr<Expr> object, const Token& name_tok)
      : object(std::move(object)), name(name_tok.lexeme()) {
    location = this->object->location;
    location.end_line = name_tok.location.end_line;
    location.end_column = name_tok.location.end_column;
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct SetExpr final : Expr {
  std::unique_ptr<Expr> object;
  std::string_view name;
  std::unique_ptr<Expr> value;

  SetExpr(std::unique_ptr<Expr> object, const Token& name_tok,
          std::unique_ptr<Expr> value)
      : object(std::move(object)),
        name(name_tok.lexeme()),
        value(std::move(value)) {
    location = this->object->location;
    location.end_line = this->value->location.end_line;
    location.end_column = this->value->location.end_column;
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct ExpressionStmt final : Stmt {
  std::unique_ptr<Expr> expr;

  explicit ExpressionStmt(std::unique_ptr<Expr> expr) : expr(std::move(expr)) {
    location = this->expr->location;
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct LetStmt final : Stmt {
  std::string_view name;
  std::unique_ptr<Expr> initializer;

  LetStmt(const Token& name_tok, std::unique_ptr<Expr> initializer)
      : name(name_tok.lexeme()), initializer(std::move(initializer)) {
    location = name_tok.location;
    if (this->initializer) {
      location.end_line = this->initializer->location.end_line;
      location.end_column = this->initializer->location.end_column;
    }
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct ConstStmt final : Stmt {
  std::string_view name;
  std::unique_ptr<Expr> initializer;

  ConstStmt(const Token& name_tok, std::unique_ptr<Expr> initializer)
      : name(name_tok.lexeme()), initializer(std::move(initializer)) {
    location = name_tok.location;
    if (this->initializer) {
      location.end_line = this->initializer->location.end_line;
      location.end_column = this->initializer->location.end_column;
    }
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct BlockStmt final : Stmt {
  std::vector<std::unique_ptr<Stmt>> statements;

  explicit BlockStmt(std::vector<std::unique_ptr<Stmt>> statements)
      : statements(std::move(statements)) {
    if (!this->statements.empty()) {
      location = this->statements.front()->location;
      location.end_line = this->statements.back()->location.end_line;
      location.end_column = this->statements.back()->location.end_column;
    }
  }

  [[nodiscard]] size_t size() const { return statements.size(); }
  [[nodiscard]] bool empty() const { return statements.empty(); }
  [[nodiscard]] const std::unique_ptr<Stmt>& back() const {
    return statements.back();
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct IfStmt final : Stmt {
  std::unique_ptr<Expr> condition;
  std::unique_ptr<Stmt> then_branch;
  std::unique_ptr<Stmt> else_branch;

  IfStmt(std::unique_ptr<Expr> condition, std::unique_ptr<Stmt> then_branch,
         std::unique_ptr<Stmt> else_branch)
      : condition(std::move(condition)),
        then_branch(std::move(then_branch)),
        else_branch(std::move(else_branch)) {
    location = this->condition->location;
    if (this->else_branch) {
      location.end_line = this->else_branch->location.end_line;
      location.end_column = this->else_branch->location.end_column;
    } else {
      location.end_line = this->then_branch->location.end_line;
      location.end_column = this->then_branch->location.end_column;
    }
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct WhileStmt final : Stmt {
  std::unique_ptr<Expr> condition;
  std::unique_ptr<Stmt> body;

  WhileStmt(std::unique_ptr<Expr> condition, std::unique_ptr<Stmt> body)
      : condition(std::move(condition)), body(std::move(body)) {
    location = this->condition->location;
    location.end_line = this->body->location.end_line;
    location.end_column = this->body->location.end_column;
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct ForStmt final : Stmt {
  std::string_view variable_name;
  std::unique_ptr<Expr> iterable;
  std::unique_ptr<Stmt> body;

  ForStmt(const Token& variable_tok, std::unique_ptr<Expr> iterable,
          std::unique_ptr<Stmt> body)
      : variable_name(variable_tok.lexeme()),
        iterable(std::move(iterable)),
        body(std::move(body)) {
    location = variable_tok.location;
    location.end_line = this->body->location.end_line;
    location.end_column = this->body->location.end_column;
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct ReturnStmt final : Stmt {
  std::unique_ptr<Expr> value;

  ReturnStmt(const Token& keyword, std::unique_ptr<Expr> value)
      : value(std::move(value)) {
    location = keyword.location;
    if (this->value) {
      location.end_line = this->value->location.end_line;
      location.end_column = this->value->location.end_column;
    }
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct FunctionStmt final : Stmt {
  std::string_view name;
  // TODO: support type annotations with params
  std::vector<std::string_view> params;
  // TODO: improve type annotation support beyond a string
  std::optional<std::string_view> return_type;
  std::unique_ptr<BlockStmt> body;

  FunctionStmt(const Token& name_tok,
               const std::vector<std::string_view>& params,
               std::unique_ptr<BlockStmt> body)
      : name(name_tok.lexeme()), params(params), body(std::move(body)) {
    location = name_tok.location;
    if (!this->body->empty()) {
      location.end_line = this->body->back()->location.end_line;
      location.end_column = this->body->back()->location.end_column;
    }
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

struct ClassStmt final : Stmt {
  std::string_view name;
  std::vector<std::unique_ptr<FunctionStmt>> methods;

  ClassStmt(const Token& name_tok,
            std::vector<std::unique_ptr<FunctionStmt>> methods)
      : name(name_tok.lexeme()), methods(std::move(methods)) {
    location = name_tok.location;
    if (!this->methods.empty()) {
      location.end_line = this->methods.back()->location.end_line;
      location.end_column = this->methods.back()->location.end_column;
    }
  }

  void accept(AstVisitor& visitor) const override { visitor.visit(*this); }
};

}  // namespace vulpes::frontend
